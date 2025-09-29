# features/Invoice_Page/invoice_details/invoice_page_controller.py

from PySide6.QtWidgets import QDialog
from features.Invoice_Page.invoice_details.invoice_details_logic import InvoiceDetailsLogic
from features.Invoice_Page.invoice_details.invoice_details_view import InvoiceDetailsWidget
from features.Invoice_Page.customer_info.customer_info_models import Customer
from features.Invoice_Page.document_selection.document_selection_models import InvoiceItem
from features.Invoice_Page.invoice_details.invoice_details_models import InvoiceDetails
from features.Invoice_Page.invoice_page_state_manager import WorkflowStateManager
from features.Invoice_Page.invoice_details.invoice_details_settings_dialog import SettingsManager, SettingsDialog


class InvoiceDetailsController:
    def __init__(self, view: InvoiceDetailsWidget, logic: InvoiceDetailsLogic,
                 state_manager: WorkflowStateManager,
                 settings_manager: SettingsManager):
        self._view = view
        self._logic = logic
        self._state_manager = state_manager
        self._settings_manager = settings_manager

        self._current_details: InvoiceDetails = None
        self._connect_signals()

    def get_view(self) -> InvoiceDetailsWidget:
        """Exposes the _view for integration into a larger UI."""
        return self._view

    def _connect_signals(self):
        """Connect signals from the _view to the controller's own slots."""
        self._view.financial_input_changed.connect(self._on_financial_input_changed)
        self._view.other_input_changed.connect(self._on_other_input_changed)
        self._view.settings_requested.connect(self._on_settings_requested)

    def prepare_and_display_data(self, customer: Customer, items: list[InvoiceItem]):
        """Public method called by MainWindow to kick off this step."""
        # 1. Display static info that never changes
        office_info = self._logic.get_static_office_info()
        self._view.display_static_info(customer, office_info)

        # 2. Ask _logic to calculate the initial DTO
        self._current_details = self._logic.create_initial_details(customer, items)

        # 3. Update the _view and the global state with the initial DTO
        self._process_update(self._current_details)

    def _process_update(self, details: InvoiceDetails):
        """A central place to handle all updates."""
        self._current_details = details
        self._view.update_display(self._current_details)
        self._state_manager.set_invoice_details(self._current_details)

    # --- Controller Slots ---

    def _on_financial_input_changed(self, field: str, value: float, mode: str):
        """
        Handles input from the toggled spinboxes and calls the appropriate logic.
        """
        if self._current_details is None:
            return

        if mode == 'percent':
            new_details = self._logic.update_with_percent_change(self._current_details, field, value)
        else:  # mode == 'amount'
            new_details = self._logic.update_with_amount_change(self._current_details, field, int(value))

        self._process_update(new_details)

    def _on_other_input_changed(self, other_data: dict):
        if self._current_details is None: return
        new_details = self._logic.update_with_other_changes(self._current_details, other_data)
        self._process_update(new_details)

    def _on_settings_requested(self):
        """
        Handles the request to open the settings dialog. Manages the dialog's
        lifecycle and triggers updates if settings are changed.
        """
        # The Controller creates and shows the dialog
        dialog = SettingsDialog(self._settings_manager, self._view)  # Parent to the view for proper positioning

        # If the user clicks "Save" (dialog is accepted)
        if dialog.exec() == QDialog.Accepted:
            # Command the View to update its appearance
            self._view.apply_settings()

            # Trigger a full recalculation of the invoice details to ensure
            # any logic changes (like the emergency cost basis) are applied.
            if self._current_details:
                # A simple way to force a recalculation is to re-run an update
                # with the existing data. The logic layer will use the new settings.
                new_details = self._logic.update_with_percent_change(
                    self._current_details, 'discount', self._current_details.discount_percent
                )
                self._process_update(new_details)