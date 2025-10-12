# features/Invoice_Page/invoice_details/invoice_details_logic.py

from features.Invoice_Page.invoice_details.invoice_details_repo import InvoiceDetailsRepository
from features.Invoice_Page.document_selection.document_selection_models import InvoiceItem
from features.Invoice_Page.invoice_details.invoice_details_models import InvoiceDetails, UserInfo
from features.Invoice_Page.invoice_details.invoice_details_settings_dialog import SettingsManager
from features.Invoice_Page.invoice_preview.invoice_preview_models import PreviewOfficeInfo

from shared.session_provider import ManagedSessionProvider, SessionManager
from shared.services.invoice_number_generator import InvoiceNumberService
from shared.orm_models.invoices_models import InvoiceData


class InvoiceDetailsLogic:
    """The pure Python 'brain' for the invoice details step."""

    def __init__(self, repo: InvoiceDetailsRepository,
                 users_engine: ManagedSessionProvider,
                 invoices_engine: ManagedSessionProvider,
                 settings_manager: SettingsManager
                 ):
        super().__init__()
        self._repo = repo
        self._users_session = users_engine
        self._invoices_session = invoices_engine
        self._settings_manager = settings_manager
        self._invoice_number_service = InvoiceNumberService(invoices_engine)
        with self._users_session() as session:
            self._office_info = self._repo.get_office_info(session)

    def create_initial_details(self, items: list[InvoiceItem]) -> InvoiceDetails:
        """Calculates all initial values for a NEW invoice."""
        invoice_number = self._invoice_number_service.get_next_invoice_number()
        details = self._create_base_details_from_items(items, invoice_number)

        default_remarks = self._settings_manager.get("default_remarks", "")
        details.remarks = default_remarks

        return self._recalculate_totals(details)

    # --- EDIT WORKFLOW METHOD ---
    def create_details_for_edit(self, items: list[InvoiceItem], original_invoice: InvoiceData) -> InvoiceDetails:
        """Calculates totals from items and populates the rest from an existing invoice."""
        # 1. Start with the base calculations from the (potentially modified) item list
        details = self._create_base_details_from_items(items, original_invoice.invoice_number)

        # 2. Override defaults with data from the original invoice
        details.emergency_cost_amount = original_invoice.emergency_cost
        details.discount_amount = original_invoice.discount_amount
        details.advance_payment_amount = original_invoice.advance_payment
        details.remarks = original_invoice.remarks
        details.delivery_date = original_invoice.delivery_date

        # 3. Back-calculate percentages so the UI controls are correct
        #    This reuses the logic from update_with_amount_change

        # Emergency Percent
        basis_setting = self._settings_manager.get("emergency_basis")
        base_emergency = details.translation_cost if basis_setting == "translation_cost" else details.total_before_variables
        if base_emergency > 0:
            details.emergency_cost_percent = (details.emergency_cost_amount / base_emergency) * 100.0

        # Discount Percent
        base_for_discount = details.total_before_variables + details.emergency_cost_amount
        if base_for_discount > 0:
            details.discount_percent = (details.discount_amount / base_for_discount) * 100.0

        # Advance Percent
        total_after_discount = base_for_discount - details.discount_amount
        if total_after_discount > 0:
            details.advance_payment_percent = (details.advance_payment_amount / total_after_discount) * 100.0

        # 4. Perform final recalculation of totals
        return self._recalculate_totals(details)

    def _create_base_details_from_items(self, items: list[InvoiceItem], invoice_number: str) -> InvoiceDetails:
        """Helper to perform the initial summation from a list of items."""
        print(f'Calculating details based on items: {items}.')
        total_documents = sum(item.quantity for item in items)
        translation_cost = sum(item.translation_price for item in items)
        confirmation_cost = sum(item.judiciary_seal_price + item.foreign_affairs_seal_price for item in items)
        office_costs = sum(item.registration_price for item in items)
        certified_copy_costs = sum(item.certified_copy_price for item in items)
        additional_issues_costs = sum(item.extra_copy_price for item in items)

        print(f'Calculated details: total documents {total_documents},'
              f' translation_cost: {translation_cost},'
              f' confirmation_cost: {confirmation_cost},'
              f' office_costs: {office_costs},'
              f' certified_copy_costs: {certified_copy_costs},'
              f' additional_issues_costs: {additional_issues_costs}.')

        return InvoiceDetails(
            invoice_number=invoice_number,
            docu_num=total_documents,
            translation_cost=translation_cost,
            confirmation_cost=confirmation_cost,
            office_costs=office_costs,
            additional_issues_costs=additional_issues_costs,
            certified_copy_costs=certified_copy_costs,
            office_info=self._office_info
        )

    def update_with_percent_change(self, details: InvoiceDetails, field: str, percent: float) -> InvoiceDetails:
        """Returns a new DTO recalculated based on a percentage change."""
        if field == 'emergency':
            basis_setting = self._settings_manager.get("emergency_basis")
            base = (details.translation_cost + details.confirmation_cost + details.office_costs +
                    details.certified_copy_costs)
            emergency_base = details.translation_cost if basis_setting == "translation_cost" else base
            amount = int(emergency_base * (percent / 100.0))
            details.emergency_cost_percent = percent
            details.emergency_cost_amount = amount

        elif field == 'discount':
            base_for_discount = (details.translation_cost + details.confirmation_cost +
                                 details.office_costs + details.certified_copy_costs +
                                 details.emergency_cost_amount)
            amount = int(base_for_discount * (percent / 100.0))
            details.discount_percent = percent
            details.discount_amount = amount

        elif field == 'advance':
            base_for_advance = (details.translation_cost + details.confirmation_cost +
                                details.office_costs + details.certified_copy_costs +
                                details.emergency_cost_amount - details.discount_amount)
            amount = int(base_for_advance * (percent / 100.0))
            details.advance_payment_percent = percent
            details.advance_payment_amount = amount

        return self._recalculate_totals(details)

    def update_with_amount_change(self, details: InvoiceDetails, field: str, amount: int) -> InvoiceDetails:
        """Returns a new DTO recalculated based on an amount change."""
        percent = 0.0
        if field == 'emergency':
            basis_setting = self._settings_manager.get("emergency_basis")
            base = (details.translation_cost + details.confirmation_cost + details.office_costs +
                    details.certified_copy_costs)
            emergency_base = details.translation_cost if basis_setting == "translation_cost" else base
            if emergency_base > 0: percent = (amount / emergency_base) * 100.0
            details.emergency_cost_amount = amount
            details.emergency_cost_percent = percent

        elif field == 'discount':
            base_for_discount = (details.translation_cost + details.confirmation_cost +
                                 details.office_costs + details.certified_copy_costs +
                                 details.emergency_cost_amount)
            if base_for_discount > 0: percent = (amount / base_for_discount) * 100.0
            details.discount_amount = amount
            details.discount_percent = percent

        elif field == 'advance':
            base_for_advance = (details.translation_cost + details.confirmation_cost +
                                details.office_costs + details.certified_copy_costs +
                                details.emergency_cost_amount - details.discount_amount)
            if base_for_advance > 0: percent = (amount / base_for_advance) * 100.0
            details.advance_payment_amount = amount
            details.advance_payment_percent = percent

        return self._recalculate_totals(details)

    def update_with_other_changes(self, details: InvoiceDetails, other_data: dict) -> InvoiceDetails:
        """Returns a new DTO updated with miscellaneous data."""
        details.delivery_date = other_data.get('delivery_date', details.delivery_date)
        details.src_lng = other_data.get('src_lng', details.src_lng)
        details.trgt_lng = other_data.get('trgt_lng', details.trgt_lng)
        details.remarks = other_data.get('remarks', details.remarks)
        return details

    def get_static_user_info(self) -> UserInfo:
        """Provides static user info to the controller."""
        session_data = SessionManager().get_session()
        if session_data:
            return UserInfo(
                full_name=session_data.full_name,
                role=session_data.role,
                role_fa=session_data.role_fa,
                username=session_data.username
            )

    def get_static_office_info(self) -> PreviewOfficeInfo:
        """Provides the cached office info to the controller."""
        return self._office_info

    def _recalculate_totals(self, details: InvoiceDetails) -> InvoiceDetails:
        """Private helper. The single source of truth for all financial calculations."""
        base = (details.translation_cost + details.confirmation_cost + details.office_costs +
                details.certified_copy_costs + details.additional_issues_costs)
        details.total_before_discount = base

        total_billable = base + details.emergency_cost_amount
        if details.discount_amount > total_billable:
            details.discount_amount = total_billable

        details.total_after_discount = total_billable - details.discount_amount

        if details.advance_payment_amount > details.total_after_discount:
            details.advance_payment_amount = details.total_after_discount

        details.final_amount = details.total_after_discount - details.advance_payment_amount
        return details

    def recalculate_all_variables(self, details: InvoiceDetails) -> InvoiceDetails:
        """
        Re-evaluates emergency, discount, and advance payments based on their
        currently stored percentages and the latest settings.
        """
        details = self.update_with_percent_change(details, 'emergency', details.emergency_cost_percent)
        details = self.update_with_percent_change(details, 'discount', details.discount_percent)
        details = self.update_with_percent_change(details, 'advance', details.advance_payment_percent)
        return details

    def create_empty_details(self):
        """Creates empty details for resetting the view."""
        return InvoiceDetails()
