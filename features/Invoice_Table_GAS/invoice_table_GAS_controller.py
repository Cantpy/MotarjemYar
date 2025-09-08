import logging
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox, QFileDialog, QWidget
from typing import List, Any, Optional, Callable

# Import other components
from features.Invoice_Table_GAS.invoice_table_GAS_view import InvoiceTableView, EditInvoiceDialog, SummaryDialog
from features.Invoice_Table_GAS.invoice_table_GAS_logic import InvoiceTableLogic, FileLogic, ValidationLogic
from features.Invoice_Table_GAS.invoice_table_GAS_repo import RepositoryManager
from features.Invoice_Table_GAS.invoice_table_GAS_models import InvoiceData, InvoiceSummary

logger = logging.getLogger(__name__)


# The MainController now creates the _view and handles all _logic.
class MainController(QObject):
    """
    Main controller that coordinates all components for the invoice table feature.
    It creates and manages the _view, and connects UI signals to application _logic.
    """

    def __init__(self):
        super().__init__()

        # --- Component Initialization ---
        self._repo_manager = RepositoryManager()
        self._logic = InvoiceTableLogic(self._repo_manager)
        self._file_logic = FileLogic()
        self._validation_logic = ValidationLogic()

        # The controller creates its own _view.
        self._view = InvoiceTableView()

        # --- State Management ---
        self._all_invoices: List[InvoiceData] = []
        self._filtered_invoices: List[InvoiceData] = []
        self._selected_invoice_numbers: List[str] = []
        self._doc_counts: dict = {}
        self._translator_names: List[str] = []
        self._is_column_filter_visible = False

        self._connect_signals()

    def get_widget(self) -> QWidget:
        """Returns the managed _view widget to be displayed in the main application."""
        return self._view

    def load_initial_data(self):
        """Kicks off the initial data loading process."""
        self._load_column_settings()
        self._refresh_data()

    def _connect_signals(self):
        """Connects signals from the _view to the controller's handler methods."""
        # View signals
        self._view.refresh_requested.connect(self._refresh_data)
        self._view.search_text_changed.connect(self._filter_invoices)
        self._view.selection_changed.connect(self._on_selection_changed)
        self._view.delete_invoice_requested.connect(self._delete_single_invoice)
        self._view.bulk_delete_requested.connect(self._delete_bulk_invoices)
        self._view.edit_invoice_requested.connect(self._edit_invoice)
        self._view.translator_updated.connect(self._update_translator)
        self._view.open_pdf_requested.connect(self._open_pdf)
        self._view.summary_requested.connect(self._show_summary)
        self._view.export_requested.connect(self._export_to_csv)
        self._view.toggle_column_filter_requested.connect(self._toggle_column_filters)
        self._view.column_visibility_changed.connect(self._set_column_visibility)
        self._view.window_closed.connect(self._save_column_settings)

    # --- Handlers for View Signals (Slots) ---

    def _refresh_data(self):
        try:
            self._all_invoices = self._logic.load_invoices()
            self._doc_counts = self._logic.get_all_document_counts()
            self._translator_names = self._logic.get_translator_names()
            self._filter_invoices(self._view.search_bar.text())  # Re-apply current filter
            self._view.clear_search_bar()
            self.show_success("به‌روزرسانی", f"{len(self._all_invoices)} فاکتور با موفقیت بارگذاری شد.")
        except Exception as e:
            logger.error(f"Error refreshing data: {e}")
            self.show_error("خطا", f"خطا در بارگذاری اطلاعات: {e}")

    def _filter_invoices(self, search_text: str):
        self._filtered_invoices = self._logic.search_invoices(search_text, self._all_invoices)
        self._view.update_table(self._filtered_invoices, self._doc_counts, self._translator_names)
        self._update_selection_display()

    def _on_selection_changed(self, selected_numbers: List[str]):
        self._selected_invoice_numbers = selected_numbers
        self._update_selection_display()

    def _update_selection_display(self):
        selected_count = len(self._selected_invoice_numbers)
        visible_count = len(self._filtered_invoices)
        self._view.update_selection_info(selected_count, visible_count)

    def _delete_single_invoice(self, invoice_number: str):
        if self.show_confirmation(f"آیا از حذف فاکتور شماره {invoice_number} مطمئن هستید؟"):
            if self._logic.delete_single_invoice(invoice_number):
                self.show_success("موفقیت", "فاکتور با موفقیت حذف شد.")
                self._refresh_data()
            else:
                self.show_error("خطا", "عملیات حذف فاکتور ناموفق بود.")

    def _delete_bulk_invoices(self):
        count = len(self._selected_invoice_numbers)
        if count == 0:
            self.show_error("خطا", "هیچ فاکتوری برای حذف انتخاب نشده است.")
            return

        if self.show_confirmation(f"آیا از حذف {count} فاکتور انتخاب شده مطمئن هستید؟"):
            if self._logic.delete_multiple_invoices(self._selected_invoice_numbers):
                self.show_success("موفقیت", f"{count} فاکتور با موفقیت حذف شدند.")
                self._selected_invoice_numbers.clear()
                self._refresh_data()
            else:
                self.show_error("خطا", "عملیات حذف گروهی ناموفق بود.")

    def _edit_invoice(self, invoice_number: str):
        invoice_to_edit = self._repo_manager.get_invoice_repository().get_invoice_by_number(invoice_number)
        if not invoice_to_edit:
            self.show_error("خطا", "فاکتور مورد نظر یافت نشد.")
            return

        dialog = EditInvoiceDialog(invoice_to_edit, self._view)
        if dialog.exec_():
            updated_data = dialog.get_updated_data()
            # Add validation here using self._validation_logic
            is_valid, errors = self._logic.validate_invoice_data(updated_data)
            if not is_valid:
                self.show_error("خطای اعتبارسنجی", "\n".join(errors))
                return

            if self._logic.update_invoice_data(invoice_number, updated_data):
                self.show_success("موفقیت", "فاکتور با موفقیت ویرایش شد.")
                self._refresh_data()
            else:
                self.show_error("خطا", "ویرایش فاکتور ناموفق بود.")

    def _update_translator(self, invoice_number: str, translator_name: str):
        # Optional: Add confirmation
        if self._logic.update_translator(invoice_number, translator_name):
            # No need for a success message, the UI update is enough
            self._refresh_data()  # Quick way to reflect change
        else:
            self.show_error("خطا", "به‌روزرسانی نام مترجم ناموفق بود.")

    def _open_pdf(self, invoice_number: str):
        invoice = self._repo_manager.get_invoice_repository().get_invoice_by_number(invoice_number)
        if invoice and invoice.pdf_file_path and self._file_logic.validate_pdf_path(invoice.pdf_file_path):
            self._view.open_pdf_file_path(invoice.pdf_file_path)
        else:
            if self.show_confirmation(
                    f"فایل PDF برای فاکتور {invoice_number} یافت نشد. آیا میخواهید فایل را انتخاب کنید؟"):
                file_path = self._show_file_dialog("انتخاب فایل PDF", "*.pdf")
                if file_path:
                    self._repo_manager.get_invoice_repository().update_pdf_path(invoice_number, file_path)
                    self._view.open_pdf_file_path(file_path)

    def _show_summary(self):
        summary = self._logic.get_invoice_summary()
        if summary:
            dialog = SummaryDialog(summary, self._view)
            dialog.exec_()

    def _export_to_csv(self):
        count = len(self._selected_invoice_numbers)
        if count == 0:
            self.show_error("خطا", "هیچ فاکتوری برای صدور انتخاب نشده است.")
            return

        file_path = self._show_save_dialog("ذخیره فایل CSV", "invoices.csv", "*.csv")
        if file_path:
            if self._logic.export_invoices_to_csv(self._selected_invoice_numbers, file_path):
                self.show_success("موفقیت", f"اطلاعات {count} فاکتور با موفقیت در فایل ذخیره شد.")
            else:
                self.show_error("خطا", "عملیات صدور فایل ناموفق بود.")

    # --- UI State Management ---

    def _toggle_column_filters(self):
        self._is_column_filter_visible = not self._is_column_filter_visible
        self._view.toggle_column_filter_widgets(self._is_column_filter_visible)

    def _set_column_visibility(self, col_index: int, is_visible: bool):
        self._logic.set_column_visibility(col_index, is_visible)
        self._view.set_column_visibility(col_index, is_visible)

    def _load_column_settings(self):
        # Pretend settings are loaded from a file/QSettings
        visibility_states = self._logic.load_column_settings_from_source()
        self._view.restore_column_checkboxes(visibility_states)
        for i, is_visible in enumerate(visibility_states):
            self._set_column_visibility(i, is_visible)

    def _save_column_settings(self):
        self._logic.save_column_settings_to_source()
        logger.info("Column settings saved.")

    # --- Dialog Helpers ---
    def show_confirmation(self, message: str) -> bool:
        reply = QMessageBox.question(self._view, "تایید", message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        return reply == QMessageBox.Yes

    def show_error(self, title: str, message: str):
        QMessageBox.critical(self._view, title, message)

    def show_success(self, title: str, message: str):
        QMessageBox.information(self._view, title, message)

    def _show_file_dialog(self, title: str, file_filter: str) -> Optional[str]:
        path, _ = QFileDialog.getOpenFileName(self._view, title, "", file_filter)
        return path

    def _show_save_dialog(self, title: str, default_name: str, file_filter: str) -> Optional[str]:
        path, _ = QFileDialog.getSaveFileName(self._view, title, default_name, file_filter)
        return path
