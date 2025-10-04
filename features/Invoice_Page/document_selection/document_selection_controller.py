# features/Invoice_Page/document_selection/document_selection_controller.py

from PySide6.QtWidgets import QDialog
from PySide6.QtCore import QObject, Signal

from features.Invoice_Page.document_selection.document_selection_logic import DocumentSelectionLogic
from features.Invoice_Page.document_selection.document_selection_view import DocumentSelectionWidget
from features.Invoice_Page.document_selection.document_selection_models import InvoiceItem
from features.Invoice_Page.invoice_page_state_manager import WorkflowStateManager
from features.Invoice_Page.document_selection.price_calculation_dialog import CalculationDialog
from features.Invoice_Page.document_selection.document_selection_settings_dialog import SettingsDialog


class DocumentSelectionController(QObject):
    invoice_items_changed = Signal(list)

    def __init__(self,
                 view: DocumentSelectionWidget,
                 logic: DocumentSelectionLogic,
                 state_manager: WorkflowStateManager):
        super().__init__()

        self._logic = logic
        self._view = view
        self._state_manager = state_manager

        # Initial population of the _view
        self._populate_view_completers()
        self._connect_signals()

    def get_view(self) -> DocumentSelectionWidget:
        """Exposes the _view for integration into a larger UI."""
        return self._view

    def _populate_view_completers(self):
        """Fetches all necessary data and populates all UI completers."""
        service_names = self._logic.get_all_service_names()
        self._view.populate_completer(service_names)

        history = self._logic.get_smart_search_history()
        self._view.populate_smart_completer(history)

    def _connect_signals(self):
        """Connect signals from the _view to controller slots."""
        self._view.smart_add_triggered.connect(self._on_smart_add)
        self._view.add_button_clicked.connect(self._on_add_clicked)
        self._view.edit_button_clicked.connect(self._on_edit_clicked)
        self._view.delete_button_clicked.connect(self._on_delete_clicked)
        self._view.clear_button_clicked.connect(self._on_clear_clicked)
        self._view.manual_item_updated.connect(self._on_manual_update)
        self._view.settings_button_clicked.connect(self._on_settings_clicked)

    def _refresh_view_and_emit_changes(self):
        """A new helper to bundle common refresh actions."""
        updated_items = self._logic.get_current_items()
        self._view.update_table_display(updated_items)
        self.invoice_items_changed.emit(updated_items)

    # --- Slot Implementations ---

    def _on_smart_add(self, text: str):
        """Handles the smart entry addition workflow."""
        success = self._logic.process_smart_entry(text)

        if success:
            self._refresh_view_and_emit_changes()
            self._view.clear_smart_entry()
        else:
            self._view.show_error(f"متن وارد شده قابل شناسایی نیست.\n'{text}'")
            print(f"Could not parse smart entry: '{text}'")

    def _on_add_clicked(self, service_name: str):
        """Orchestrates adding a new item, now with the dialog workflow."""
        service = self._logic.get_service_by_name(service_name)
        if not service: return

        final_item = None
        if service.type == "خدمات دیگر":
            final_item = InvoiceItem(service=service, total_price=service.base_price)
        else:
            # For complex services, we use the dialog.
            fees = self._logic.get_calculation_fees()
            dialog = CalculationDialog(service, fees)
            if dialog.exec() == QDialog.Accepted:
                final_item = dialog.result_item

        if final_item:
            self._logic.add_item(final_item)
            self._refresh_view_and_emit_changes()
            self._view.clear_service_input()

    def _on_edit_clicked(self, index: int):
        """Orchestrates editing an existing item with the dialog."""
        items = self._logic.get_current_items()
        if not (0 <= index < len(items)): return

        item_to_edit = items[index]
        if item_to_edit.service.type == "خدمات دیگر": return

        fees = self._logic.get_calculation_fees()
        dialog = CalculationDialog(item_to_edit.service, fees, item_to_edit=item_to_edit)
        if dialog.exec() == QDialog.Accepted:
            final_item = dialog.result_item
            final_item.unique_id = item_to_edit.unique_id
            self._logic.update_item_at_index(index, final_item)
            self._refresh_view_and_emit_changes()

    def _on_delete_clicked(self, index: int):
        """Handles deletion of an item at a specific index."""
        self._logic.delete_item_at_index(index)
        self._refresh_view_and_emit_changes()

    def _on_clear_clicked(self):
        """Clears all items from the invoice."""
        self._logic.clear_all_items()
        self._refresh_view_and_emit_changes()

    def _on_manual_update(self, item: InvoiceItem, new_price: int, new_remarks: str):
        """Handles updates to manually-entered items."""
        self._logic.update_manual_item(item, new_price, new_remarks)
        self._refresh_view_and_emit_changes()

    def _on_settings_clicked(self):
        """Opens the settings dialog and handles the update process."""
        all_fixed_prices = self._logic.get_all_fixed_prices()

        dialog = SettingsDialog(all_fixed_prices)
        if dialog.exec() == QDialog.Accepted:
            updated_data = dialog.updated_prices

            # 1. Save the changes to the database
            self._logic.update_fixed_prices(updated_data)

            # 2. CRITICAL: Tell the logic layer to reload its entire cache
            self._logic.refresh_all_data()

            # 3. CRITICAL: Tell the view to update its completers with the new data
            self._populate_view_completers()

            print("Fixed prices updated and application state refreshed successfully.")

    def reset_view(self):
        """Clears all fields in the invoice details view."""
        self._on_clear_clicked()
