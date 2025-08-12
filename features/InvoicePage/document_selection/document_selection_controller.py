from typing import Optional
from PySide6.QtCore import QObject, Signal
from features.InvoicePage.document_selection.document_selection_view import DocumentSelectionView
from features.InvoicePage.price_calculation.price_calculation_controller import PriceDialogController
from features.InvoicePage.document_selection.document_selection_logic import  (DocumentLogic, PriceCalculationLogic,
                                                                               InvoiceLogic)
from features.InvoicePage.document_selection.document_selection_models import DocumentItem


class DocumentSelectionController(QObject):
    """Main controller for document selection application"""

    # Signals
    document_added = Signal(object)  # DocumentItem
    document_removed = Signal(int)  # row index
    invoice_cleared = Signal()

    def __init__(self, document_logic: DocumentLogic, price_logic: PriceCalculationLogic, parent=None):
        super().__init__(parent)

        # Logic components
        self.document_logic = document_logic
        self.price_logic = price_logic
        self.invoice_logic = InvoiceLogic()

        # UI components
        self.view: Optional[DocumentSelectionView] = None
        self.price_dialog_controller: Optional[PriceDialogController] = None

        # Initialize price dialog controller
        self.price_dialog_controller = PriceDialogController(
            self.document_logic,
            self.price_logic,
            self
        )

    def create_view(self, parent=None) -> DocumentSelectionView:
        """Create and setup the main view"""
        self.view = DocumentSelectionView(parent)
        self._connect_view_signals()
        self._initialize_view_data()
        return self.view

    def _connect_view_signals(self):
        """Connect view signals to controller methods"""
        if not self.view:
            return

        self.view.add_document_requested.connect(self._on_add_document_requested)
        self.view.remove_document_requested.connect(self._on_remove_document_requested)
        self.view.clear_requested.connect(self._on_clear_requested)
        self.view.document_selected.connect(self._on_document_selected)

    def _initialize_view_data(self):
        """Initialize view with data"""
        if not self.view:
            return

        # Setup autocomplete suggestions
        suggestions = self.document_logic.get_document_suggestions("")
        self.view.setup_autocomplete(suggestions)

        # Focus on input field
        self.view.focus_document_input()

    def _on_add_document_requested(self, document_name: str):
        """Handle add document request"""
        if not self.view:
            return

        # Validate document name
        if not document_name.strip():
            self.view.show_error_message("خطا", "لطفاً نام سند را وارد کنید")
            return

        # Check if document exists in database
        if not self.document_logic.validate_document_name(document_name):
            self.view.show_error_message(
                "خطا",
                f"سند '{document_name}' در پایگاه داده موجود نیست"
            )
            return

        # Show price dialog
        result = self.price_dialog_controller.show_dialog(document_name, self.view)

        if result.accepted and result.document_item:
            # Add to view
            self.view.add_document_to_table(result.document_item)

            # Add to logic
            self.invoice_logic.add_item(result.document_item)

            # Clear input and emit signal
            self.view.clear_document_input()
            self.document_added.emit(result.document_item)

            # Show success message
            self.view.show_info_message("موفق", "سند با موفقیت اضافه شد")

        elif result.error_message:
            self.view.show_error_message("خطا", result.error_message)

    def _on_remove_document_requested(self, row_index: int):
        """Handle remove document request"""
        if not self.view:
            return

        # Get document name for confirmation
        document_name = self.view.get_document_at_row(row_index)
        if not document_name:
            return

        # Confirm removal
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self.view,
            "تایید حذف",
            f"آیا از حذف سند '{document_name}' مطمئن هستید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Remove from view
            if self.view.remove_document_from_table(row_index):
                # Remove from logic
                self.invoice_logic.remove_item(row_index)

                # Emit signal
                self.document_removed.emit(row_index)

                # Show success message
                self.view.show_info_message("موفق", "سند با موفقیت حذف شد")

    def _on_clear_requested(self):
        """Handle clear all request"""
        if not self.view:
            return

        # Clear view
        self.view.clear_table()

        # Clear logic
        self.invoice_logic.clear_items()

        # Emit signal
        self.invoice_cleared.emit()

        # Show success message
        self.view.show_info_message("موفق", "همه اسناد پاک شدند")

    def _on_document_selected(self, document_name: str):
        """Handle document selection (double-click)"""
        if not self.view:
            return

        # Set document name in input for editing
        self.view.set_document_input_text(document_name)
        self.view.focus_document_input()

    def get_invoice_total(self) -> int:
        """Get total invoice amount"""
        return self.invoice_logic.get_total_amount()

    def get_invoice_items_count(self) -> int:
        """Get number of items in invoice"""
        return self.invoice_logic.get_items_count()

    def get_invoice_items(self) -> list:
        """Get all invoice items"""
        return self.invoice_logic.items.copy()

    def export_invoice_data(self) -> dict:
        """Export invoice data for external use"""
        return {
            'items': [
                {
                    'name': item.name,
                    'type': item.document_type.value,
                    'count': item.count,
                    'judiciary_seal': item.judiciary_seal,
                    'foreign_affairs_seal': item.foreign_affairs_seal,
                    'total_price': item.total_price,
                    'remarks': item.remarks
                }
                for item in self.invoice_logic.items
                for item in self.invoice_logic.items
            ],
            'total_amount': self.get_invoice_total(),
            'items_count': self.get_invoice_items_count()
        }

    def show_invoice_summary(self):
        """Show invoice summary dialog"""
        if not self.view:
            return

        if self.get_invoice_items_count() == 0:
            self.view.show_info_message("اطلاعات", "هیچ سندی در فاکتور موجود نیست")
            return

        # Show total amount
        self.view.show_total_amount()

    def search_documents(self, partial_name: str) -> list:
        """Search for documents matching partial name"""
        return self.document_logic.get_document_suggestions(partial_name)

    def refresh_autocomplete(self):
        """Refresh autocomplete suggestions"""
        if self.view:
            suggestions = self.document_logic.get_document_suggestions("")
            self.view.update_autocomplete_suggestions(suggestions)

    def validate_document_name(self, name: str) -> bool:
        """Validate if document name exists"""
        return self.document_logic.validate_document_name(name)

    def get_view(self) -> Optional[DocumentSelectionView]:
        """Get the main view"""
        return self.view

    def cleanup(self):
        """Clean up resources"""
        if self.view:
            self.view.close()
            self.view = None

        # Clear invoice data
        self.invoice_logic.clear_items()
