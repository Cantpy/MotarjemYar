# features/Invoice_Page/invoice_details/invoice_page_controller.py

from features.Invoice_Page.invoice_details.invoice_details_logic import InvoiceDetailsLogic
from features.Invoice_Page.invoice_details.invoice_details_view import InvoiceDetailsWidget
from features.Invoice_Page.customer_info.customer_info_models import Customer
from features.Invoice_Page.document_selection.document_selection_models import InvoiceItem
from features.Invoice_Page.invoice_details.invoice_details_models import InvoiceDetails
from features.Invoice_Page.invoice_page_state_manager import WorkflowStateManager


class InvoiceDetailsController:
    def __init__(self, view: InvoiceDetailsWidget, logic: InvoiceDetailsLogic, state_manager: WorkflowStateManager):
        self._view = view
        self._logic = logic
        self._state_manager = state_manager

        self._current_details: InvoiceDetails = None
        self._connect_signals()

    def get_view(self) -> InvoiceDetailsWidget:
        """Exposes the view for integration into a larger UI."""
        return self._view

    def _connect_signals(self):
        """Connect signals from the view to the controller's own slots."""
        self._view.percent_changed.connect(self._on_percent_changed)
        self._view.amount_changed.connect(self._on_amount_changed)
        self._view.other_input_changed.connect(self._on_other_input_changed)

    def prepare_and_display_data(self, customer: Customer, items: list[InvoiceItem]):
        """Public method called by MainWindow to kick off this step."""
        # 1. Display static info that never changes
        office_info = self._logic.get_static_office_info()
        self._view.display_static_info(customer, office_info)

        # 2. Ask logic to calculate the initial DTO
        self._current_details = self._logic.create_initial_details(customer, items)

        # 3. Update the view and the global state with the initial DTO
        self._process_update(self._current_details)

    def _process_update(self, details: InvoiceDetails):
        """A central place to handle all updates."""
        self._current_details = details
        self._view.update_display(self._current_details)
        self._state_manager.set_invoice_details(self._current_details)

    # --- Controller Slots ---

    def _on_percent_changed(self, field: str, percent: float):
        if self._current_details is None: return
        new_details = self._logic.update_with_percent_change(self._current_details, field, percent)
        self._process_update(new_details)

    def _on_amount_changed(self, field: str, amount: int):
        if self._current_details is None: return
        new_details = self._logic.update_with_amount_change(self._current_details, field, amount)
        self._process_update(new_details)

    def _on_other_input_changed(self, other_data: dict):
        if self._current_details is None: return
        new_details = self._logic.update_with_other_changes(self._current_details, other_data)
        self._process_update(new_details)
    #
    # def prepare_and_display_data(self, customer: Customer, items: list[InvoiceItem]):
    #     """Public method called by MainWindow to kick off this step."""
    #     # Pass data to both the _view (for static display) and the _logic (for calculations)
    #     self._view.display_static_info(customer, self._logic._repo.get_office_info())
    #     self._logic.prepare_initial_details(customer, items)
    #
    # def _on_logic_updated(self, details):
    #     """When _logic recalculates, update the _view and the global state."""
    #     self._view.update_display(details)
    #     self._state_manager.set_invoice_details(details)
    #
    # def get_widget(self) -> InvoiceDetailsWidget:
    #     return self._view
