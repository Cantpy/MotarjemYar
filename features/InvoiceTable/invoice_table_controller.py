from typing import List, Dict, Any, Optional, Callable
from PySide6.QtCore import QObject, Signal, QSettings
from PySide6.QtWidgets import QMessageBox, QFileDialog
from features.InvoiceTable.invoice_table_models import InvoiceData, InvoiceSummary
from features.InvoiceTable.invoice_table_logic import (InvoiceLogic, FileLogic, ValidationLogic, SearchLogic, SortLogic,
                                                       ExportLogic, BulkOperationLogic)
from features.InvoiceTable.invoice_table_repo import RepositoryManager
import logging

logger = logging.getLogger(__name__)


class InvoiceController(QObject):
    """Controller for managing invoice table operations"""

    # Signals for view updates
    data_loaded = Signal(list)  # List[InvoiceData]
    data_filtered = Signal(list)  # List[InvoiceData]
    invoice_updated = Signal(str)  # invoice_number
    invoice_deleted = Signal(list)  # List[invoice_numbers]
    selection_changed = Signal(int)  # selected_count
    error_occurred = Signal(str, str)  # title, message
    success_message = Signal(str, str)  # title, message

    def __init__(self, invoices_db_url: str, users_db_url: str, parent=None):
        super().__init__(parent)

        # Initialize components
        self.repo_manager = RepositoryManager(invoices_db_url, users_db_url)
        self.logic = InvoiceLogic(self.repo_manager)

        # Data storage
        self.invoices: List[InvoiceData] = []
        self.filtered_invoices: List[InvoiceData] = []
        self.selected_invoices: List[str] = []

        # Settings
        self.settings = QSettings("InvoiceApp", "ColumnSettings")

        # Load initial data
        self.load_data()

    def load_data(self):
        """Load invoice data from repository"""
        try:
            self.invoices = self.logic.load_invoices()
            self.filtered_invoices = self.invoices.copy()
            self.data_loaded.emit(self.invoices)
            logger.info(f"Loaded {len(self.invoices)} invoices")
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            self.error_occurred.emit("خطا در بارگذاری", f"خطا در بارگذاری اطلاعات: {e}")

    def refresh_data(self):
        """Refresh data from database"""
        self.load_data()
        self.clear_selection()

    def search_invoices(self, search_text: str):
        """Filter invoices based on search text"""
        try:
            search_terms = SearchLogic.create_search_terms(search_text)

            if not search_terms:
                self.filtered_invoices = self.invoices.copy()
            else:
                self.filtered_invoices = [
                    invoice for invoice in self.invoices
                    if SearchLogic.matches_any_field(invoice, search_terms)
                ]

            self.data_filtered.emit(self.filtered_invoices)
            logger.debug(f"Filtered to {len(self.filtered_invoices)} invoices")

        except Exception as e:
            logger.error(f"Error in search: {e}")
            self.error_occurred.emit("خطا در جستجو", f"خطا در جستجو: {e}")

    def sort_invoices(self, column: str, reverse: bool = False):
        """Sort invoices by column"""
        try:
            self.filtered_invoices = SortLogic.sort_invoices(
                self.filtered_invoices, column, reverse
            )
            self.data_filtered.emit(self.filtered_invoices)
        except Exception as e:
            logger.error(f"Error sorting: {e}")
            self.error_occurred.emit("خطا در مرتب‌سازی", f"خطا در مرتب‌سازی: {e}")

    def update_selection(self, selected_invoice_numbers: List[str]):
        """Update selected invoices"""
        self.selected_invoices = selected_invoice_numbers
        self.selection_changed.emit(len(selected_invoice_numbers))

    def clear_selection(self):
        """Clear all selections"""
        self.selected_invoices.clear()
        self.selection_changed.emit(0)

    def delete_selected_invoices(self, confirm_callback: Callable[[str], bool]):
        """Delete selected invoices with confirmation"""
        try:
            selected_count = len(self.selected_invoices)

            # Validate bulk delete
            is_valid, error_msg = BulkOperationLogic.validate_bulk_delete(selected_count)
            if not is_valid:
                self.error_occurred.emit("خطا", error_msg)
                return

            # Get confirmation
            confirmation_msg = BulkOperationLogic.create_bulk_confirmation_message(
                'delete', selected_count
            )

            if not confirm_callback(confirmation_msg):
                return

            # Perform deletion
            success = self.logic.delete_multiple_invoices(self.selected_invoices)

            if success:
                deleted_invoices = self.selected_invoices.copy()
                self.clear_selection()
                self.refresh_data()
                self.invoice_deleted.emit(deleted_invoices)
                self.success_message.emit(
                    "حذف انجام شد",
                    f"{selected_count} فاکتور با موفقیت حذف شد"
                )
            else:
                self.error_occurred.emit("خطا", "خطا در حذف فاکتورها")

        except Exception as e:
            logger.error(f"Error deleting invoices: {e}")
            self.error_occurred.emit("خطا", f"خطا در حذف: {e}")

    def delete_single_invoice(self, invoice_number: str, confirm_callback: Callable[[str], bool]):
        """Delete a single invoice with confirmation"""
        try:
            confirmation_msg = f"آیا از حذف فاکتور شماره {invoice_number} مطمئن هستید؟"

            if not confirm_callback(confirmation_msg):
                return

            success = self.logic.delete_single_invoice(invoice_number)

            if success:
                self.refresh_data()
                self.invoice_deleted.emit([invoice_number])
                self.success_message.emit("حذف انجام شد", "فاکتور با موفقیت حذف شد")
            else:
                self.error_occurred.emit("خطا", "خطا در حذف فاکتور")

        except Exception as e:
            logger.error(f"Error deleting invoice: {e}")
            self.error_occurred.emit("خطا", f"خطا در حذف: {e}")

    def update_invoice_data(self, invoice_number: str, updates: Dict[str, Any]):
        """Update invoice data"""
        try:
            # Validate data
            is_valid, errors = self.logic.validate_invoice_data(updates)
            if not is_valid:
                error_msg = "\n".join(errors)
                self.error_occurred.emit("خطا در اعتبارسنجی", error_msg)
                return

            success = self.logic.update_invoice_data(invoice_number, updates)

            if success:
                self.refresh_data()
                self.invoice_updated.emit(invoice_number)
                self.success_message.emit("به‌روزرسانی انجام شد", "اطلاعات با موفقیت به‌روزرسانی شد")
            else:
                self.error_occurred.emit("خطا", "خطا در به‌روزرسانی اطلاعات")

        except Exception as e:
            logger.error(f"Error updating invoice: {e}")
            self.error_occurred.emit("خطا", f"خطا در به‌روزرسانی: {e}")

    def update_translator(self, invoice_number: str, translator_name: str, confirm_callback: Callable[[str], bool]):
        """Update translator for invoice with confirmation"""
        try:
            confirmation_msg = (
                f"آیا مطمئن هستید که می‌خواهید '{translator_name}' را "
                f"به‌عنوان مترجم این فاکتور انتخاب کنید؟"
            )

            if not confirm_callback(confirmation_msg):
                return

            success = self.logic.update_translator(invoice_number, translator_name)

            if success:
                self.refresh_data()
                self.invoice_updated.emit(invoice_number)
            else:
                self.error_occurred.emit("خطا", "خطا در ذخیره نام مترجم")

        except Exception as e:
            logger.error(f"Error updating translator: {e}")
            self.error_occurred.emit("خطا", f"خطا در به‌روزرسانی مترجم: {e}")

    def get_translator_names(self) -> List[str]:
        """Get available translator names"""
        try:
            return self.logic.get_translator_names()
        except Exception as e:
            logger.error(f"Error getting translator names: {e}")
            return ["نامشخص"]

    def get_document_count(self, invoice_number: str) -> int:
        """Get document count for invoice"""
        try:
            return self.logic.get_document_count(invoice_number)
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0

    def export_selected_to_csv(self, file_path_callback: Callable[[], Optional[str]]):
        """Export selected invoices to CSV"""
        try:
            if not self.selected_invoices:
                self.error_occurred.emit("هشدار", "هیچ فاکتوری انتخاب نشده است")
                return

            file_path = file_path_callback()
            if not file_path:
                return

            success = self.logic.export_invoices_to_csv(self.selected_invoices, file_path)

            if success:
                self.success_message.emit(
                    "صادرات انجام شد",
                    f"{len(self.selected_invoices)} فاکتور با موفقیت صادر شد"
                )
            else:
                self.error_occurred.emit("خطا", "خطا در صادرات فایل")

        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            self.error_occurred.emit("خطا", f"خطا در صادرات: {e}")

    def get_invoice_summary(self) -> Optional[InvoiceSummary]:
        """Get invoice summary statistics"""
        try:
            return self.logic.get_invoice_summary()
        except Exception as e:
            logger.error(f"Error getting summary: {e}")
            self.error_occurred.emit("خطا", "خطا در دریافت اطلاعات خلاصه")
            return None

    def set_column_visibility(self, column_index: int, visible: bool):
        """Set column visibility and save to settings"""
        try:
            self.logic.set_column_visibility(column_index, visible)
            self.settings.setValue(f"column_visible_{column_index}", visible)
        except Exception as e:
            logger.error(f"Error setting column visibility: {e}")

    def is_column_visible(self, column_index: int) -> bool:
        """Check if column is visible"""
        try:
            return self.logic.is_column_visible(column_index)
        except Exception as e:
            logger.error(f"Error checking column visibility: {e}")
            return True

    def get_column_names(self) -> List[str]:
        """Get column names"""
        return self.logic.get_column_names()

    def load_column_settings(self):
        """Load column visibility settings"""
        try:
            column_names = self.get_column_names()
            for i in range(len(column_names)):
                saved_value = self.settings.value(f"column_visible_{i}", True, type=bool)
                self.logic.set_column_visibility(i, saved_value)
        except Exception as e:
            logger.error(f"Error loading column settings: {e}")

    def save_column_settings(self):
        """Save column visibility settings"""
        try:
            self.settings.sync()
        except Exception as e:
            logger.error(f"Error saving column settings: {e}")


class FileController(QObject):
    """Controller for file operations"""

    # Signals
    pdf_found = Signal(str)  # file_path
    pdf_not_found = Signal(str)  # invoice_number
    pdf_path_updated = Signal(str, str)  # invoice_number, new_path

    def __init__(self, repo_manager: RepositoryManager, parent=None):
        super().__init__(parent)
        self.repo_manager = repo_manager

    def open_pdf(self, invoice_number: str, pdf_path: Optional[str] = None):
        """Open PDF file for invoice"""
        try:
            if not pdf_path:
                # Get PDF path from database
                invoice = self.repo_manager.get_invoice_repository().get_invoice_by_number(invoice_number)
                if not invoice or not invoice.pdf_file_path:
                    self.pdf_not_found.emit(invoice_number)
                    return
                pdf_path = invoice.pdf_file_path

            # Check if file exists
            if FileLogic.validate_pdf_path(pdf_path):
                self.pdf_found.emit(pdf_path)
            else:
                # Try to recover
                recovered_path = FileLogic.recover_lost_pdf(invoice_number)
                if recovered_path:
                    self.update_pdf_path(invoice_number, recovered_path)
                    self.pdf_found.emit(recovered_path)
                else:
                    self.pdf_not_found.emit(invoice_number)

        except Exception as e:
            logger.error(f"Error opening PDF: {e}")
            self.pdf_not_found.emit(invoice_number)

    def browse_for_pdf(self, invoice_number: str, file_dialog_callback: Callable[[], Optional[str]]):
        """Browse for PDF file and update path"""
        try:
            file_path = file_dialog_callback()
            if file_path and FileLogic.validate_pdf_path(file_path):
                self.update_pdf_path(invoice_number, file_path)
                self.pdf_found.emit(file_path)
        except Exception as e:
            logger.error(f"Error browsing for PDF: {e}")

    def update_pdf_path(self, invoice_number: str, new_path: str):
        """Update PDF path in database"""
        try:
            success = self.repo_manager.get_invoice_repository().update_pdf_path(invoice_number, new_path)
            if success:
                self.pdf_path_updated.emit(invoice_number, new_path)
        except Exception as e:
            logger.error(f"Error updating PDF path: {e}")


class ValidationController(QObject):
    """Controller for validation operations"""

    def __init__(self, parent=None):
        super().__init__(parent)

    def validate_national_id(self, national_id: str) -> bool:
        """Validate national ID"""
        return ValidationLogic.validate_national_id(national_id)

    def validate_phone_number(self, phone: str) -> bool:
        """Validate phone number"""
        return ValidationLogic.validate_phone_number(phone)

    def validate_amount(self, amount_str: str) -> tuple[bool, float]:
        """Validate amount string"""
        return ValidationLogic.validate_amount(amount_str)


class MainController(QObject):
    """Main controller that coordinates other controllers"""

    def __init__(self, invoices_db_url: str, users_db_url: str, parent_widget=None):
        super().__init__()

        self.parent_widget = parent_widget

        # Initialize sub-controllers
        self.invoice_controller = InvoiceController(invoices_db_url, users_db_url, self)
        self.file_controller = FileController(self.invoice_controller.repo_manager, self)
        self.validation_controller = ValidationController(self)

        # Connect signals
        self._connect_signals()

    def _connect_signals(self):
        """Connect signals between controllers"""
        # File controller signals
        self.file_controller.pdf_path_updated.connect(
            self.invoice_controller.refresh_data
        )

    def get_invoice_controller(self) -> InvoiceController:
        """Get invoice controller"""
        return self.invoice_controller

    def get_file_controller(self) -> FileController:
        """Get file controller"""
        return self.file_controller

    def get_validation_controller(self) -> ValidationController:
        """Get validation controller"""
        return self.validation_controller

    def show_confirmation_dialog(self, message: str) -> bool:
        """Show confirmation dialog"""
        if not self.parent_widget:
            return True

        reply = QMessageBox.question(
            self.parent_widget,
            "تایید",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return reply == QMessageBox.Yes

    def show_error_dialog(self, title: str, message: str):
        """Show error dialog"""
        if self.parent_widget:
            QMessageBox.critical(self.parent_widget, title, message)

    def show_success_dialog(self, title: str, message: str):
        """Show success dialog"""
        if self.parent_widget:
            QMessageBox.information(self.parent_widget, title, message)

    def show_file_dialog(self, title: str, file_filter: str) -> Optional[str]:
        """Show file dialog"""
        if not self.parent_widget:
            return None

        file_path, _ = QFileDialog.getOpenFileName(
            self.parent_widget,
            title,
            "",
            file_filter
        )
        return file_path if file_path else None

    def show_save_dialog(self, title: str, default_name: str, file_filter: str) -> Optional[str]:
        """Show save file dialog"""
        if not self.parent_widget:
            return None

        file_path, _ = QFileDialog.getSaveFileName(
            self.parent_widget,
            title,
            default_name,
            file_filter
        )
        return file_path if file_path else None
