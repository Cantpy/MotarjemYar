# invoice_details/controller.py
from features.Invoice_Page_GAS.invoice_details_GAS.invoice_details_logic import InvoiceDetailsLogic
from features.Invoice_Page_GAS.invoice_details_GAS.invoice_details_view import InvoiceDetailsWidget
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_models import Customer
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_models import InvoiceItem


class InvoiceDetailsController:
    def __init__(self, state_manager):
        self._logic = InvoiceDetailsLogic()
        self._view = InvoiceDetailsWidget()
        self.state_manager = state_manager

        # Connect the layers
        self._logic.details_updated.connect(self._on_logic_updated)

        # --- Connect the new, specific signals to the new logic slots ---
        self._view.percent_changed.connect(self._logic.on_percent_changed)
        self._view.amount_changed.connect(self._logic.on_amount_changed)
        self._view.other_input_changed.connect(self._logic.on_other_input_changed)

    def prepare_and_display_data(self, customer: Customer, items: list[InvoiceItem]):
        """Public method called by MainWindow to kick off this step."""
        # Pass data to both the view (for static display) and the logic (for calculations)
        self._view.display_static_info(customer, self._logic._repo.get_office_info())
        self._logic.prepare_initial_details(customer, items)

    def _on_logic_updated(self, details):
        """When logic recalculates, update the view and the global state."""
        self._view.update_display(details)
        self.state_manager.set_invoice_details(details)

    def get_widget(self) -> InvoiceDetailsWidget:
        return self._view
