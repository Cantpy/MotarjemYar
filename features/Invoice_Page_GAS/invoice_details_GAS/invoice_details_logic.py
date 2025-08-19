# invoice_details/logic.py
from PySide6.QtCore import QObject, Signal
from features.Invoice_Page_GAS.invoice_details_GAS.invoice_details_repo import InvoiceDetailsRepository
from features.Invoice_Page_GAS.invoice_details_GAS.invoice_details_models import InvoiceDetails
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_models import Customer
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_models import InvoiceItem
from shared.utils.date_utils import get_persian_date


class InvoiceDetailsLogic(QObject):
    """The 'brain' for the invoice details step."""
    details_updated = Signal(object)

    def __init__(self):
        super().__init__()
        self._repo = InvoiceDetailsRepository()
        self._current_details: InvoiceDetails = None

    def prepare_initial_details(self, customer: Customer, items: list[InvoiceItem]):
        """Calculates all initial values and prepares the InvoiceDetails object."""
        invoice_number = self._repo.get_next_invoice_number()
        office_info = self._repo.get_office_info()

        # --- FIX: Calculate Total Documents Correctly ---
        # Instead of len(items), we now sum the quantity of each item.
        # This includes the main quantity and any extra copies for each item.
        total_documents = sum(item.quantity for item in items)

        # Sum costs from invoice items (this part is already correct)
        translation_cost = sum(item.translation_price * item.quantity for item in items)  # Multiply by quantity
        confirmation_cost = sum(
            (item.judiciary_seal_price * item.quantity) + (item.foreign_affairs_seal_price * item.page_count) for item
            in items)
        office_costs = sum(item.registration_price * item.quantity for item in items)
        certified_copy_costs = sum(item.certified_copy_price * item.quantity for item in items)
        # Note: Extra copy price is handled separately in the dialog's total, not here.

        # Assemble the initial state object with the correct document count
        self._current_details = InvoiceDetails(
            invoice_number=invoice_number,
            docu_num=total_documents,
            issue_date=get_persian_date(),
            translation_cost=translation_cost,
            confirmation_cost=confirmation_cost,
            office_costs=office_costs,
            certified_copy_costs=certified_copy_costs,
            office_info=office_info
        )

        self._recalculate_totals()

    def update_from_view(self, changed_data: dict):
        """Receives user input changes from the view and recalculates."""
        if not self._current_details: return

        # Update the state object with the new values from the UI
        self._current_details.delivery_date = changed_data.get('delivery_date', self._current_details.delivery_date)
        self._current_details.src_lng = changed_data.get('src_lng', self._current_details.src_lng)
        self._current_details.trgt_lng = changed_data.get('trgt_lng', self._current_details.trgt_lng)
        self._current_details.emergency_cost = changed_data.get('emergency_cost', self._current_details.emergency_cost)
        self._current_details.discount_percent = changed_data.get('discount_percent',
                                                                  self._current_details.discount_percent)
        self._current_details.advance_payment = changed_data.get('advance_payment_amount',
                                                                 self._current_details.advance_payment)
        self._current_details.remarks = changed_data.get('remarks', self._current_details.remarks)

        self._recalculate_totals()

    def on_percent_changed(self, field_name: str, percent: float):
        """Handles updates when a PERCENTAGE spinbox is changed by the user."""
        if not self._current_details: return

        # --- The base for percentage calculation is the sum of fixed service costs ---
        base_total = (self._current_details.translation_cost + self._current_details.confirmation_cost +
                      self._current_details.office_costs + self._current_details.certified_copy_costs)

        amount = int(base_total * (percent / 100.0))

        if field_name == 'discount':
            self._current_details.discount_percent = percent
            self._current_details.discount_amount = amount
        elif field_name == 'emergency':
            self._current_details.emergency_cost_percent = percent
            self._current_details.emergency_cost_amount = amount
        elif field_name == 'advance':
            # Advance payment percentage is based on the final payable amount
            payable_total = (base_total + self._current_details.emergency_cost_amount -
                             self._current_details.discount_amount)
            amount = int(payable_total * (percent / 100.0))
            self._current_details.advance_payment_percent = percent
            self._current_details.advance_payment_amount = amount

        self._recalculate_totals()

    def on_amount_changed(self, field_name: str, amount: int):
        """Handles updates when an AMOUNT spinbox is changed by the user."""
        if not self._current_details: return

        base_total = (self._current_details.translation_cost + self._current_details.confirmation_cost +
                      self._current_details.office_costs + self._current_details.certified_copy_costs)

        percent = 0.0

        if field_name == 'discount':
            if base_total > 0: percent = (amount / base_total) * 100.0
            self._current_details.discount_amount = amount
            self._current_details.discount_percent = percent
        elif field_name == 'emergency':
            if base_total > 0: percent = (amount / base_total) * 100.0
            self._current_details.emergency_cost_amount = amount
            self._current_details.emergency_cost_percent = percent
        elif field_name == 'advance':
            payable_total = (base_total + self._current_details.emergency_cost_amount -
                             self._current_details.discount_amount)
            if payable_total > 0: percent = (amount / payable_total) * 100.0
            self._current_details.advance_payment_amount = amount
            self._current_details.advance_payment_percent = percent

        self._recalculate_totals()

    def on_other_input_changed(self, changed_data: dict):
        """Handles simple inputs like dates and remarks."""
        if not self._current_details: return
        self._current_details.delivery_date = changed_data.get('delivery_date', self._current_details.delivery_date)
        self._current_details.src_lng = changed_data.get('src_lng', self._current_details.src_lng)
        self._current_details.trgt_lng = changed_data.get('trgt_lng', self._current_details.trgt_lng)
        self._current_details.remarks = changed_data.get('remarks', self._current_details.remarks)
        self.details_updated.emit(self._current_details)

    def _recalculate_totals(self):
        """The single source of truth for financial calculations."""
        d = self._current_details

        base_total = (d.translation_cost + d.confirmation_cost +
                      d.office_costs + d.certified_copy_costs)

        d.total_before_discount = base_total + d.emergency_cost_amount
        d.total_after_discount = d.total_before_discount - d.discount_amount

        # Cap advance payment to the payable amount
        if d.advance_payment_amount > d.total_after_discount:
            d.advance_payment_amount = d.total_after_discount
            if d.total_after_discount > 0:
                # Recalculate percent based on capped amount
                payable_total = d.total_after_discount + d.advance_payment_amount  # Recalculate original payable
                d.advance_payment_percent = (
                                                        d.advance_payment_amount / payable_total) * 100.0 if payable_total > 0 else 0.0
            else:
                d.advance_payment_percent = 0.0

        d.final_amount = d.total_after_discount - d.advance_payment_amount

        self.details_updated.emit(self._current_details)

    # def on_percent_changed(self, field_name: str, percent: float):
    #     """Handles updates when a PERCENTAGE spinbox is changed by the user."""
    #     if not self._current_details: return
    #
    #     total = self._current_details.total_before_variables
    #     amount = int(total * (percent / 100.0))
    #
    #     if field_name == 'discount':
    #         self._current_details.discount_percent = percent
    #         self._current_details.discount_amount = amount
    #     elif field_name == 'emergency':
    #         self._current_details.emergency_cost_percent = percent
    #         self._current_details.emergency_cost_amount = amount
    #     elif field_name == 'advance':
    #         self._current_details.advance_payment_percent = percent
    #         self._current_details.advance_payment_amount = amount
    #
    #     self._recalculate_totals()
    #
    # def on_amount_changed(self, field_name: str, amount: int):
    #     """Handles updates when an AMOUNT spinbox is changed by the user."""
    #     if not self._current_details: return
    #
    #     total = self._current_details.total_before_variables
    #     percent = 0.0
    #     if total > 0:
    #         percent = (amount / total) * 100.0
    #
    #     if field_name == 'discount':
    #         self._current_details.discount_amount = amount
    #         self._current_details.discount_percent = percent
    #     elif field_name == 'emergency':
    #         self._current_details.emergency_cost = amount
    #         self._current_details.emergency_cost_percent = percent
    #     elif field_name == 'advance':
    #         self._current_details.advance_payment = amount
    #         self._current_details.advance_payment_percent = percent
    #
    #     self._recalculate_totals()
    #
    # def on_other_input_changed(self, changed_data: dict):
    #     """Handles simple inputs like dates and remarks."""
    #     if not self._current_details: return
    #     self._current_details.delivery_date = changed_data.get('delivery_date')
    #     self._current_details.remarks = changed_data.get('remarks')
    #     # ... update other simple fields ...
    #     self._recalculate_totals()
    #
    # def _recalculate_totals(self):
    #     """The single source of truth for financial calculations."""
    #     d = self._current_details
    #
    #     # Base total is now just the sum of service-related costs
    #     base_total = (d.translation_cost + d.confirmation_cost +
    #                   d.office_costs + d.certified_copy_costs)
    #
    #     # The new total before discount includes the emergency cost amount
    #     d.total_before_variables = base_total + d.emergency_cost
    #
    #     d.total_before_variables = d.total_before_variables - d.discount_amount
    #
    #     # Cap advance payment to the payable amount
    #     if d.advance_payment > d.total_before_variables:
    #         d.advance_payment = d.total_before_variables
    #         # Recalculate the percentage based on the capped amount
    #         if d.total_before_variables > 0:
    #             d.advance_payment_percent = (d.advance_payment / d.total_before_variables) * 100.0
    #         else:
    #             d.advance_payment_percent = 0.0
    #
    #     d.final_amount = d.total_before_variables - d.advance_payment
    #
    #     self.details_updated.emit(self._current_details)
