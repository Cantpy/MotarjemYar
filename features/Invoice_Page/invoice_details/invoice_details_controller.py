# features/Invoice_Page/invoice_details/invoice_page_controller.py

from PySide6.QtWidgets import QDialog
from features.Invoice_Page.invoice_details.invoice_details_logic import InvoiceDetailsLogic
from features.Invoice_Page.invoice_details.invoice_details_view import InvoiceDetailsWidget
from features.Invoice_Page.customer_info.customer_info_models import Customer
from features.Invoice_Page.document_selection.document_selection_models import InvoiceItem
from features.Invoice_Page.invoice_details.invoice_details_models import InvoiceDetails
from features.Invoice_Page.invoice_page_state_manager import WorkflowStateManager
from features.Invoice_Page.invoice_details.invoice_details_settings_dialog import SettingsManager, SettingsDialog
from shared.orm_models.invoices_models import InvoiceData


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
        self._state_manager.invoice_items_updated.connect(self._on_invoice_items_updated)

    def prepare_and_display_data(self, customer: Customer, items: list[InvoiceItem]):
        """Public method for a NEW INVOICE to kick off this step."""
        office_info = self._logic.get_static_office_info()
        user_info = self._logic.get_static_user_info()
        self._view.display_static_info(customer, office_info, user_info)

        self._current_details = self._logic.create_initial_details(items)
        self._process_update(self._current_details)

    # --- NEW METHOD for EDIT WORKFLOW ---
    def prepare_and_display_data_for_edit(self, customer: Customer, items: list[InvoiceItem],
                                          original_invoice: InvoiceData):
        """Public method for an EDITED INVOICE to kick off this step."""
        office_info = self._logic.get_static_office_info()
        user_info = self._logic.get_static_user_info()
        self._view.display_static_info(customer, office_info, user_info)

        # Call the new logic method to pre-populate from original data
        self._current_details = self._logic.create_details_for_edit(items, original_invoice)
        self._process_update(self._current_details)

    def validate(self) -> (bool, str):
        """
        Checks if the essential data in the invoice details is valid.
        """
        self._view.clear_errors()
        delivery_date_text = self._view.delivery_date_edit.text()

        if not delivery_date_text or delivery_date_text.strip() == "":
            self._view.highlight_error('delivery_date')
            error_msg = "تاریخ تحویل مشخص نشده است. لطفا یک تاریخ معتبر انتخاب کنید."
            return False, error_msg

        return True, ""

    def reset_view(self):
        """Clears all fields in the invoice details view."""
        empty_details = self._logic.create_empty_details()
        self._view.update_display(empty_details)
        self._view.delivery_date_edit.clear()
        print("VIEW RESET: Invoice Details view cleared.")

    def _process_update(self, details: InvoiceDetails):
        """A central place to handle all updates."""
        self._current_details = details
        self._view.update_display(self._current_details)
        self._state_manager.set_invoice_details(self._current_details)

    def _on_invoice_items_updated(self, updated_items: list[InvoiceItem]):
        if self._current_details:
            print("InvoiceDetailsController: Detected updated items, refreshing details view.")
            self._current_details.items = updated_items
            self._process_update(self._current_details)

    def _on_financial_input_changed(self, field: str, value: float, mode: str):
        if self._current_details is None: return

        if mode == 'percent':
            new_details = self._logic.update_with_percent_change(self._current_details, field, value)
        else:
            new_details = self._logic.update_with_amount_change(self._current_details, field, int(value))

        self._process_update(new_details)

    def _on_other_input_changed(self, other_data: dict):
        if self._current_details is None: return
        new_details = self._logic.update_with_other_changes(self._current_details, other_data)
        self._process_update(new_details)

    def _on_settings_requested(self):
        dialog = SettingsDialog(self._settings_manager, self._view)
        if dialog.exec() == QDialog.Accepted:
            self._view.apply_settings()
            if self._current_details:
                new_details = self._logic.recalculate_all_variables(self._current_details)
                self._process_update(new_details)
