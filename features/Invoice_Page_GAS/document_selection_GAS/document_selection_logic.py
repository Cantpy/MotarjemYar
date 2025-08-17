# document_selection/logic.py
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QDialog
from typing import List
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_repo import DocumentSelectionRepository
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_models import Service, FixedPrice, InvoiceItem
from features.Invoice_Page_GAS.document_selection_GAS.price_calculation_dialog import CalculationDialog


class DocumentSelectionLogic(QObject):
    # This signal tells the view when it needs to update.
    invoice_list_updated = Signal(list)
    operation_successful = Signal()

    def __init__(self):
        super().__init__()
        self._repo = DocumentSelectionRepository()
        self._services_map = {s.name: s for s in self._repo.get_all_services()}
        self._calculation_fees = self._repo.get_calculation_fees()

        # --- STATE is now managed here, not in the view ---
        self._current_invoice_items: List[InvoiceItem] = []

    def get_all_service_names(self) -> List[str]:
        """Provides just the names for the view's completer."""
        return list(self._services_map.keys())

    def add_service_by_name(self, name: str):
        """
        This is a "slot" that the view's signal will connect to.
        It contains all the logic for adding a new item.
        """
        service = self._services_map.get(name)
        if not service: return

        new_item = None
        if service.type == "خدمات دیگر":
            # Logic for simple items
            new_item = InvoiceItem(service=service, quantity=1, total_price=service.base_price)
        else:
            # Logic for complex items that need the dialog
            dialog = CalculationDialog(service, self._calculation_fees)
            if dialog.exec() == QDialog.Accepted:
                new_item = dialog.result_item

        if new_item:
            self._current_invoice_items.append(new_item)
            self.invoice_list_updated.emit(self._current_invoice_items)
            self.operation_successful.emit()

    def update_manual_item(self, item_to_update: InvoiceItem, new_price: int, new_remarks: str):
        """Updates an existing 'Other Service' item."""
        for i, item in enumerate(self._current_invoice_items):
            if item is item_to_update:
                item.total_price = new_price
                item.remarks = new_remarks
                # Emit the signal to reflect the change in the UI
                self.invoice_list_updated.emit(self._current_invoice_items)
                break

    def delete_item_at_index(self, index: int):
        """Deletes an item from the list by its index."""
        if 0 <= index < len(self._current_invoice_items):
            del self._current_invoice_items[index]
            self.invoice_list_updated.emit(self._current_invoice_items)

    def clear_all_items(self):
        """Clears the entire list of items."""
        self._current_invoice_items.clear()
        self.invoice_list_updated.emit(self._current_invoice_items)

    def edit_item_at_index(self, index: int):
        """
        Opens the calculation dialog pre-filled with an existing item's data
        and replaces the item upon success.
        """
        if not (0 <= index < len(self._current_invoice_items)):
            return

        item_to_edit = self._current_invoice_items[index]

        # We can't edit "Other Services" with this dialog
        if item_to_edit.service.type == "خدمات دیگر":
            # In a real app, you might show a message box here
            return

        # Open the dialog, passing the existing item to its constructor
        dialog = CalculationDialog(item_to_edit.service, self._calculation_fees, item_to_edit=item_to_edit)
        if dialog.exec() == QDialog.Accepted:
            self._current_invoice_items[index] = dialog.result_item
            self.invoice_list_updated.emit(self._current_invoice_items)
            self.operation_successful.emit()
