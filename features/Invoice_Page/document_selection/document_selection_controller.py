# features/Invoice_Page/document_selection/document_selection_controller.py

from PySide6.QtWidgets import QDialog
from PySide6.QtCore import QObject, Signal

from features.Invoice_Page.document_selection.document_selection_logic import DocumentSelectionLogic
from features.Invoice_Page.document_selection.document_selection_view import DocumentSelectionWidget
from features.Invoice_Page.document_selection.document_selection_models import InvoiceItem
from features.Invoice_Page.invoice_page_state_manager import WorkflowStateManager
from features.Invoice_Page.document_selection.price_calculation_dialog import CalculationDialog


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

        # Initial population of the view
        self._view.populate_completer(self._logic.get_all_service_names())
        self._connect_signals()

    def get_view(self) -> DocumentSelectionWidget:
        """Exposes the view for integration into a larger UI."""
        return self._view

    def _connect_signals(self):
        """Connect signals from the view to controller slots."""
        self._view.add_button_clicked.connect(self._on_add_clicked)
        self._view.edit_button_clicked.connect(self._on_edit_clicked)
        self._view.delete_button_clicked.connect(self._on_delete_clicked)
        self._view.clear_button_clicked.connect(self._on_clear_clicked)
        self._view.manual_item_updated.connect(self._on_manual_update)

    def _refresh_view(self):
        """A helper method to get the latest data and update the view."""
        updated_items = self._logic.get_current_items()
        self._view.update_table_display(updated_items)

    def _on_add_clicked(self, service_name: str):
        """Orchestrates adding a new item, now with the dialog workflow."""
        service = self._logic.get_service_by_name(service_name)
        if not service: return

        final_item = None
        if service.type == "خدمات دیگر":
            item_shell = InvoiceItem(service=service, total_price=service.base_price)
            final_item = self._logic.calculate_invoice_item(item_shell)
        else:
            # For complex items, the CONTROLLER shows the dialog
            fees = self._logic.get_calculation_fees()
            dialog = CalculationDialog(service, fees)
            if dialog.exec() == QDialog.Accepted:
                # 1. Get the raw user input from the dialog
                item_shell = dialog.result_item
                # 2. Ask the _logic layer to perform the authoritative calculation
                final_item = self._logic.calculate_invoice_item(item_shell)

        if final_item:
            # The _logic returns the new, complete list
            updated_items = self._logic.add_item(final_item)

            # Refresh the local view AND emit the signal for the outside world
            self._view.update_table_display(updated_items)
            self._view.clear_service_input()
            self.invoice_items_changed.emit(updated_items)

    def _on_edit_clicked(self, index: int):
        """Orchestrates editing an existing item with the dialog."""
        items = self._logic.get_current_items()
        if not (0 <= index < len(items)): return

        item_to_edit = items[index]
        if item_to_edit.service.type == "خدمات دیگر": return

        fees = self._logic.get_calculation_fees()
        # Pass the existing item to pre-populate the dialog
        dialog = CalculationDialog(item_to_edit.service, fees, item_to_edit=item_to_edit)
        if dialog.exec() == QDialog.Accepted:
            item_shell = dialog.result_item
            # Ensure the unique ID is preserved for the update
            item_shell.unique_id = item_to_edit.unique_id
            final_item = self._logic.calculate_invoice_item(item_shell)
            self._logic.update_item_at_index(index, final_item)
            self._refresh_view()

    def _on_delete_clicked(self, index: int):
        updated_items = self._logic.delete_item_at_index(index)
        self._view.update_table_display(updated_items)
        self.invoice_items_changed.emit(updated_items)

    def _on_clear_clicked(self):
        updated_items = self._logic.clear_all_items()
        self._view.update_table_display(updated_items)
        self.invoice_items_changed.emit(updated_items)

    def _on_manual_update(self, item: InvoiceItem, new_price: int, new_remarks: str):
        updated_items = self._logic.update_manual_item(item, new_price, new_remarks)
        self._view.update_table_display(updated_items)
        self.invoice_items_changed.emit(updated_items)
