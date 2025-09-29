# features/Invoice_Page/invoice_details/invoice_details_logic.py

from features.Invoice_Page.invoice_details.invoice_details_repo import InvoiceDetailsRepository
from features.Invoice_Page.customer_info.customer_info_models import Customer
from features.Invoice_Page.document_selection.document_selection_models import InvoiceItem
from features.Invoice_Page.invoice_details.invoice_details_models import OfficeInfo, InvoiceDetails
from features.Invoice_Page.invoice_details.invoice_details_settings_dialog import SettingsManager

from shared.utils.date_utils import get_persian_date
from shared.session_provider import ManagedSessionProvider


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
        with self._users_session() as session:
            self._office_info = self._repo.get_office_info(session)

    def create_initial_details(self, customer: Customer, items: list[InvoiceItem]) -> InvoiceDetails:
        """Calculates all initial values and returns the initial InvoiceDetails DTO."""
        with self._invoices_session() as session:
            invoice_number = self._repo.get_next_invoice_number(session)

        total_documents = sum(item.quantity for item in items)
        translation_cost = sum(item.translation_price for item in items)
        confirmation_cost = sum(item.judiciary_seal_price + item.foreign_affairs_seal_price for item in items)
        office_costs = sum(item.registration_price for item in items)
        certified_copy_costs = sum(item.certified_copy_price for item in items)

        details = InvoiceDetails(
            invoice_number=invoice_number,
            docu_num=total_documents,
            issue_date=get_persian_date(),
            translation_cost=translation_cost,
            confirmation_cost=confirmation_cost,
            office_costs=office_costs,
            certified_copy_costs=certified_copy_costs,
            office_info=self._office_info
        )

        # The initial calculation is performed on the new DTO
        return self._recalculate_totals(details)

    def update_with_percent_change(self, details: InvoiceDetails, field: str, percent: float) -> InvoiceDetails:
        """Returns a new DTO recalculated based on a percentage change."""

        if field == 'discount':
            base = details.translation_cost + details.confirmation_cost + details.office_costs + details.certified_copy_costs
            amount = int(base * (percent / 100.0))
            details.discount_percent = percent
            details.discount_amount = amount
        elif field == 'emergency':
            basis_setting = self._settings_manager.get("emergency_basis")
            base = details.translation_cost + details.confirmation_cost + details.office_costs + details.certified_copy_costs
            emergency_base = details.translation_cost if basis_setting == "translation_cost" else base
            amount = int(emergency_base * (percent / 100.0))
            details.emergency_cost_percent = percent
            details.emergency_cost_amount = amount
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
        base = details.translation_cost + details.confirmation_cost + details.office_costs + details.certified_copy_costs
        percent = 0.0

        if field == 'discount':
            if base > 0: percent = (amount / base) * 100.0
            details.discount_amount = amount
            details.discount_percent = percent
        elif field == 'emergency':
            basis_setting = self._settings_manager.get("emergency_basis")
            base = details.translation_cost + details.confirmation_cost + details.office_costs + details.certified_copy_costs

            emergency_base = details.translation_cost if basis_setting == "translation_cost" else base

            if emergency_base > 0:
                percent = (amount / emergency_base) * 100.0
            else:
                percent = 0.0
            details.emergency_cost_amount = amount
            details.emergency_cost_percent = percent
        elif field == 'advance':
            payable = (base + details.emergency_cost_amount - details.discount_amount)
            if payable > 0: percent = (amount / payable) * 100.0
            details.advance_payment_amount = amount
            details.advance_payment_percent = percent

        return self._recalculate_totals(details)

    def update_with_other_changes(self, details: InvoiceDetails, other_data: dict) -> InvoiceDetails:
        """Returns a new DTO updated with miscellaneous data."""
        details.delivery_date = other_data.get('delivery_date', details.delivery_date)
        details.src_lng = other_data.get('src_lng', details.src_lng)
        details.trgt_lng = other_data.get('trgt_lng', details.trgt_lng)
        details.remarks = other_data.get('remarks', details.remarks)
        # No recalculation needed for these fields, so we just return the modified object
        return details

    def get_static_office_info(self) -> OfficeInfo:
        """Provides the cached office info to the controller."""
        return self._office_info

    def _recalculate_totals(self, details: InvoiceDetails) -> InvoiceDetails:
        """Private helper. The single source of truth for all financial calculations."""
        base = details.translation_cost + details.confirmation_cost + details.office_costs + details.certified_copy_costs
        details.total_before_discount = base
        payable_before_advance = (base + details.emergency_cost_amount) - details.discount_amount
        details.total_after_discount = payable_before_advance

        # Business rule: Advance payment cannot be more than the amount owed
        if details.advance_payment_amount > details.total_after_discount:
            details.advance_payment_amount = details.total_after_discount

        details.final_amount = details.total_after_discount - details.advance_payment_amount
        return details
