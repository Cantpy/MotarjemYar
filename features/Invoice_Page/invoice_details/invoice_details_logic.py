# features/Invoice_Page/invoice_details/invoice_details_logic.py

from features.Invoice_Page.invoice_details.invoice_details_repo import InvoiceDetailsRepository
from features.Invoice_Page.customer_info.customer_info_models import Customer
from features.Invoice_Page.document_selection.document_selection_models import InvoiceItem
from features.Invoice_Page.invoice_details.invoice_details_models import OfficeInfo, InvoiceDetails

from shared.utils.date_utils import get_persian_date
from shared.session_provider import SessionProvider


class InvoiceDetailsLogic:
    """The pure Python 'brain' for the invoice details step."""
    def __init__(self, repo: InvoiceDetailsRepository, session_provider: SessionProvider):
        super().__init__()
        self._repo = repo
        self._session_provider = session_provider
        with self._session_provider.users() as session:
            self._office_info = self._repo.get_office_info(session)

    def create_initial_details(self, customer: Customer, items: list[InvoiceItem]) -> InvoiceDetails:
        """Calculates all initial values and returns the initial InvoiceDetails DTO."""
        with self._session_provider.invoices() as session:
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
        base = details.translation_cost + details.confirmation_cost + details.office_costs + details.certified_copy_costs
        amount = int(base * (percent / 100.0))

        if field == 'discount':
            details.discount_percent = percent
            details.discount_amount = amount
        elif field == 'emergency':
            details.emergency_cost_percent = percent
            details.emergency_cost_amount = amount
        elif field == 'advance':
            # Advance is based on the final payable amount *before* the advance itself
            payable = (base + details.emergency_cost_amount - details.discount_amount)
            amount = int(payable * (percent / 100.0))
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
            if base > 0: percent = (amount / base) * 100.0
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
        details.total_before_discount = base + details.emergency_cost_amount
        details.total_after_discount = details.total_before_discount - details.discount_amount

        # Business rule: Advance payment cannot be more than the amount owed
        if details.advance_payment_amount > details.total_after_discount:
            details.advance_payment_amount = details.total_after_discount

        details.final_amount = details.total_after_discount - details.advance_payment_amount
        return details

    #
    # def prepare_initial_details(self, customer: Customer, items: list[InvoiceItem]):
    #     """Calculates all initial values and prepares the InvoiceDetails object."""
    #     invoice_number = self._repo.get_next_invoice_number(self._session_provider.invoices)
    #     office_info = self._repo.get_office_info(self._session_provider.users)
    #
    #     # Calculate Total Documents
    #     total_documents = sum(item.quantity for item in items)
    #
    #     # Sum costs from invoice items (this part is already correct)
    #     translation_cost = sum(item.translation_price * item.quantity for item in items)  # Multiply by quantity
    #     confirmation_cost = sum(
    #         (item.judiciary_seal_price * item.quantity) + (item.foreign_affairs_seal_price * item.page_count) for item
    #         in items)
    #     office_costs = sum(item.registration_price * item.quantity for item in items)
    #     certified_copy_costs = sum(item.certified_copy_price * item.quantity for item in items)
    #     # Note: Extra copy price is handled separately in the dialog's total, not here.
    #
    #     # Assemble the initial state object with the correct document count
    #     self._current_details = InvoiceDetails(
    #         invoice_number=invoice_number,
    #         docu_num=total_documents,
    #         issue_date=get_persian_date(),
    #         translation_cost=translation_cost,
    #         confirmation_cost=confirmation_cost,
    #         office_costs=office_costs,
    #         certified_copy_costs=certified_copy_costs,
    #         office_info=office_info
    #     )
    #
    #     self._recalculate_totals()
    #
    # def update_from_view(self, changed_data: dict):
    #     """Receives user input changes from the _view and recalculates."""
    #     if not self._current_details: return
    #
    #     # Update the state object with the new values from the UI
    #     self._current_details.delivery_date = changed_data.get('delivery_date', self._current_details.delivery_date)
    #     self._current_details.src_lng = changed_data.get('src_lng', self._current_details.src_lng)
    #     self._current_details.trgt_lng = changed_data.get('trgt_lng', self._current_details.trgt_lng)
    #     self._current_details.emergency_cost = changed_data.get('emergency_cost', self._current_details.emergency_cost)
    #     self._current_details.discount_percent = changed_data.get('discount_percent',
    #                                                               self._current_details.discount_percent)
    #     self._current_details.advance_payment = changed_data.get('advance_payment_amount',
    #                                                              self._current_details.advance_payment)
    #     self._current_details.remarks = changed_data.get('remarks', self._current_details.remarks)
    #
    #     self._recalculate_totals()
    #
    # def on_percent_changed(self, field_name: str, percent: float):
    #     """Handles updates when a PERCENTAGE spinbox is changed by the user."""
    #     if not self._current_details: return
    #
    #     # --- The base for percentage calculation is the sum of fixed service costs ---
    #     base_total = (self._current_details.translation_cost + self._current_details.confirmation_cost +
    #                   self._current_details.office_costs + self._current_details.certified_copy_costs)
    #
    #     amount = int(base_total * (percent / 100.0))
    #
    #     if field_name == 'discount':
    #         self._current_details.discount_percent = percent
    #         self._current_details.discount_amount = amount
    #     elif field_name == 'emergency':
    #         self._current_details.emergency_cost_percent = percent
    #         self._current_details.emergency_cost_amount = amount
    #     elif field_name == 'advance':
    #         # Advance payment percentage is based on the final payable amount
    #         payable_total = (base_total + self._current_details.emergency_cost_amount -
    #                          self._current_details.discount_amount)
    #         amount = int(payable_total * (percent / 100.0))
    #         self._current_details.advance_payment_percent = percent
    #         self._current_details.advance_payment_amount = amount
    #
    #     self._recalculate_totals()
    #
    # def on_amount_changed(self, field_name: str, amount: int):
    #     """Handles updates when an AMOUNT spinbox is changed by the user."""
    #     if not self._current_details: return
    #
    #     base_total = (self._current_details.translation_cost + self._current_details.confirmation_cost +
    #                   self._current_details.office_costs + self._current_details.certified_copy_costs)
    #
    #     percent = 0.0
    #
    #     if field_name == 'discount':
    #         if base_total > 0: percent = (amount / base_total) * 100.0
    #         self._current_details.discount_amount = amount
    #         self._current_details.discount_percent = percent
    #     elif field_name == 'emergency':
    #         if base_total > 0: percent = (amount / base_total) * 100.0
    #         self._current_details.emergency_cost_amount = amount
    #         self._current_details.emergency_cost_percent = percent
    #     elif field_name == 'advance':
    #         payable_total = (base_total + self._current_details.emergency_cost_amount -
    #                          self._current_details.discount_amount)
    #         if payable_total > 0: percent = (amount / payable_total) * 100.0
    #         self._current_details.advance_payment_amount = amount
    #         self._current_details.advance_payment_percent = percent
    #
    #     self._recalculate_totals()
    #
    # def on_other_input_changed(self, changed_data: dict):
    #     """Handles simple inputs like dates and remarks."""
    #     if not self._current_details: return
    #     self._current_details.delivery_date = changed_data.get('delivery_date', self._current_details.delivery_date)
    #     self._current_details.src_lng = changed_data.get('src_lng', self._current_details.src_lng)
    #     self._current_details.trgt_lng = changed_data.get('trgt_lng', self._current_details.trgt_lng)
    #     self._current_details.remarks = changed_data.get('remarks', self._current_details.remarks)
    #     self.details_updated.emit(self._current_details)
    #
    # def _recalculate_totals(self):
    #     """The single source of truth for financial calculations."""
    #     d = self._current_details
    #
    #     base_total = (d.translation_cost + d.confirmation_cost +
    #                   d.office_costs + d.certified_copy_costs)
    #
    #     d.total_before_discount = base_total + d.emergency_cost_amount
    #     d.total_after_discount = d.total_before_discount - d.discount_amount
    #
    #     # Cap advance payment to the payable amount
    #     if d.advance_payment_amount > d.total_after_discount:
    #         d.advance_payment_amount = d.total_after_discount
    #         if d.total_after_discount > 0:
    #             # Recalculate percent based on capped amount
    #             payable_total = d.total_after_discount + d.advance_payment_amount  # Recalculate original payable
    #             d.advance_payment_percent = ((d.advance_payment_amount / payable_total)
    #                                          * 100.0) if payable_total > 0 else 0.0
    #         else:
    #             d.advance_payment_percent = 0.0
    #
    #     d.final_amount = d.total_after_discount - d.advance_payment_amount
    #
    #     self.details_updated.emit(self._current_details)
