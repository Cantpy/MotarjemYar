# features/Invoice_Table/invoice_table_controller.py

import logging
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QFileDialog
from typing import List, Optional
from dataclasses import asdict

from features.Invoice_Table.invoice_table_view import InvoiceTableView
from features.Invoice_Table.invoice_table_deleted_invoices_dialog import DeletedInvoicesDialog
from features.Invoice_Table.invoice_table_summary_dialog import InvoiceSummaryDialog
from features.Invoice_Table.invoice_table_edit_dialog import EditInvoiceDialog
from features.Invoice_Table.invoice_table_logic import InvoiceLogic
from features.Invoice_Table.invoice_table_models import InvoiceData

from shared import show_question_message_box, show_error_message_box, show_information_message_box
from shared.session_provider import SessionManager

logger = logging.getLogger(__name__)


# The InvoiceTableController now creates the _view and handles all _logic.
class InvoiceTableController(QObject):
    """
    Main controller that coordinates all components for the invoice table feature.
    It creates and manages the _view, and connects UI signals to application _logic.
    """
    request_deep_edit_navigation = Signal(InvoiceData, list)

    def __init__(self, view: InvoiceTableView, logic: InvoiceLogic):
        super().__init__()

        # --- Component Initialization ---
        self._logic = logic
        self._view = view

        # --- State Management ---
        self._all_invoices: List[InvoiceData] = []
        self._filtered_invoices: List[InvoiceData] = []
        self._selected_invoice_numbers: List[str] = []
        self._doc_counts: dict = {}
        self._translator_names: List[str] = []
        self._is_column_filter_visible = False

        self._connect_signals()

    def get_view(self) -> InvoiceTableView:
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
        self._view.invoice_double_clicked.connect(self._show_invoice_summary)
        self._view.search_text_changed.connect(self._filter_invoices)
        self._view.selection_changed.connect(self._on_selection_changed)
        self._view.select_all_toggled.connect(self._on_select_all_toggled)
        self._view.delete_invoice_requested.connect(self._delete_single_invoice)
        self._view.bulk_delete_requested.connect(self._delete_bulk_invoices)
        self._view.show_deleted_requested.connect(self._show_deleted_invoices)
        self._view.edit_invoice_requested.connect(self._edit_invoice)
        self._view.deep_edit_invoice_requested.connect(self._handle_deep_edit_request)
        self._view.translator_updated.connect(self._update_translator)
        self._view.open_pdf_requested.connect(self._open_pdf)
        self._view.summary_requested.connect(self._show_invoice_summary)
        self._view.export_requested.connect(self._export_to_csv)
        self._view.toggle_column_filter_requested.connect(self._toggle_column_filters)
        self._view.column_visibility_changed.connect(self._set_column_visibility)
        self._view.window_closed.connect(self._save_column_settings)

    # --- Handlers for View Signals (Slots) ---

    def _refresh_data(self):
        try:
            self._all_invoices = self._logic.invoice.get_all_invoices()
            self._doc_counts = self._logic.invoice.get_document_counts()
            self._translator_names = self._logic.invoice.get_translator_names()
            self._filter_invoices(self._view.search_bar.text())

            self._all_invoices.sort(key=lambda inv: (inv.issue_date, inv.id), reverse=False)
            # self._view.clear_search_bar() # Removed to not clear user search on refresh

        except Exception as e:
            logger.error(f"Error refreshing data: {e}")
            show_error_message_box(self._view, "خطا", f"خطا در بارگذاری اطلاعات: {e}")

    def _filter_invoices(self, search_text: str):
        self._filtered_invoices = self._logic.search.search(search_text, self._all_invoices)
        self._view.update_table(self._filtered_invoices, self._doc_counts, self._translator_names)
        self._update_selection_display()

    def _on_select_all_toggled(self, is_checked: bool):
        """Handles the 'Select All' checkbox state change."""
        self._view.set_all_rows_selected(is_checked)

    def _on_selection_changed(self, selected_numbers: List[str]):
        self._selected_invoice_numbers = selected_numbers
        self._update_selection_display()

    def _update_selection_display(self):
        selected_count = len(self._selected_invoice_numbers)
        visible_count = len(self._filtered_invoices)
        self._view.update_selection_info(selected_count, visible_count)

    def _get_current_user_name(self) -> str:
        """Retrieves the full name or username of the currently logged-in user."""
        user_info = SessionManager().get_session()
        if user_info:
            return user_info.full_name or user_info.username
        return "نامشخص"

    def _delete_single_invoice(self, invoice_number: str):
        if not invoice_number:
            show_error_message_box(self._view, "خطا", "فاکتور موردنظر یافت نشد.")
            return

        def do_delete():
            # --- MODIFICATION START ---
            deleter_name = self._get_current_user_name()
            failed_deletions = self._logic.invoice.delete_invoices([invoice_number], deleter_name)
            # --- MODIFICATION END ---

            if not failed_deletions:
                show_information_message_box(parent=self._view, title="موفقیت", message="فاکتور با موفقیت حذف شد.")
                self._refresh_data()
            else:
                show_error_message_box(self._view, "خطا", f"حذف فاکتور {invoice_number} ناموفق بود.")

        show_question_message_box(parent=self._view, title="حذف فاکتور",
                                  message=f"آیا از حذف فاکتور شماره {invoice_number} مطمئن هستید؟",
                                  button_1="بله", button_2="انصراف",
                                  yes_func=do_delete)

    def _delete_bulk_invoices(self):
        count = len(self._selected_invoice_numbers)
        if count == 0:
            show_error_message_box(self._view, "خطا", "هیچ فاکتوری برای حذف انتخاب نشده است.")
            return

        def do_bulk_delete():
            # --- MODIFICATION START ---
            deleter_name = self._get_current_user_name()
            failed_deletions = self._logic.invoice.delete_invoices(self._selected_invoice_numbers, deleter_name)
            # --- MODIFICATION END ---

            if not failed_deletions:
                show_information_message_box(self._view,
                                             "موفقیت", f"{count} فاکتور با موفقیت حذف شدند.")
            else:
                success_count = count - len(failed_deletions)
                error_message = f"{success_count} فاکتور با موفقیت حذف شد.\n"
                error_message += "فاکتورهای زیر حذف نشدند:\n"
                error_message += "\n".join(failed_deletions)
                show_error_message_box(self._view, "عملیات حذف ناقص بود", error_message)

            self._selected_invoice_numbers.clear()
            self._refresh_data()

        show_question_message_box(parent=self._view, title="حذف گروهی",
                                  message=f"آیا از حذف {count} فاکتور انتخاب شده مطمئن هستید؟",
                                  button_1="بله", button_2="انصراف",
                                  yes_func=do_bulk_delete)

    def _edit_invoice(self, invoice_number: str):
        # Fetch full invoice details, including items
        invoice_details = self._logic.invoice.get_invoice_with_details(invoice_number)
        if not invoice_details or not invoice_details[0]:
            show_error_message_box(self._view, "خطا", "فاکتور مورد نظر برای ویرایش یافت نشد.")
            return

        invoice_to_edit, items_to_edit = invoice_details

        # Use the new, powerful dialog
        dialog = EditInvoiceDialog(invoice_to_edit, items_to_edit, self._view)
        if dialog.exec_():
            updated_data, history_records = dialog.get_changes()

            if not updated_data:
                show_information_message_box(self._view, "توجه", "هیچ تغییری برای ذخیره وجود نداشت.")
                return

            # --- MODIFICATION START ---
            # Create a full representation of the invoice for validation.
            # 1. Start with the original data as a dictionary.
            final_data_for_validation = asdict(invoice_to_edit)

            # 2. Apply the user's changes on top of it.
            final_data_for_validation.update(updated_data)

            # 3. Validate the complete, final object.
            is_valid, errors = self._logic.validation.validate_invoice_update(final_data_for_validation)
            # --- MODIFICATION END ---

            if not is_valid:
                # This error message will now only appear for legitimate validation errors.
                show_error_message_box(self._view, "خطای اعتبارسنجی", "\n".join(errors))
                return

            # Perform the update using ONLY the changed data for efficiency.
            update_success = self._logic.invoice.update_invoice_data(invoice_number, updated_data)
            log_success = self._logic.invoice.log_invoice_edits(history_records)

            if update_success:
                show_information_message_box(self._view, "موفقیت", "فاکتور با موفقیت ویرایش شد.")
                if not log_success:
                    show_error_message_box(self._view, "خطای لاگ", "تغییرات ذخیره شد اما تاریخچه ثبت نشد.")
                self._refresh_data()
            else:
                show_error_message_box(self._view, "خطا", "ویرایش فاکتور ناموفق بود.")

    def _update_translator(self, invoice_number: str, translator_name: str):
        if self._logic.invoice.update_translator(invoice_number, translator_name):
            self._refresh_data()
        else:
            show_error_message_box(self._view, "خطا", "به‌روزرسانی نام مترجم ناموفق بود.")

    def _open_pdf(self, invoice_number: str):
        invoice = self._logic.invoice.get_invoice_by_number(invoice_number)
        if invoice and invoice.pdf_file_path and self._logic.file.validate_pdf_path(invoice.pdf_file_path):
            self._view.open_pdf_file_path(invoice.pdf_file_path)
        else:
            def replace_file():
                file_path = self._show_file_dialog("انتخاب فایل PDF", "*.pdf")
                if file_path:
                    self._logic.invoice.update_pdf_path(invoice_number, file_path)
                    self._view.open_pdf_file_path(file_path)

            show_question_message_box(parent=self._view, title="فایل یافت نشد",
                                      message=f"هیچ فایلی برای فاکتور {invoice_number} یافت نشد."
                                              f" آیا میخواهید فایل را انتخاب کنید؟",
                                      button_1="بله", button_2="خیر",
                                      yes_func=replace_file)

    def _export_to_csv(self):
        """Export selected invoices to CSV file."""
        count = len(self._selected_invoice_numbers)

        is_valid, message = self._logic.validation.validate_bulk_delete(count)
        if not is_valid:
            show_error_message_box(self._view, "خطا", "هیچ فاکتوری انتخاب نشده است.")
            return

        def export_to_excel():
            file_path, _ = QFileDialog.getSaveFileName(
                self._view,
                "ذخیره فایل CSV",
                "",
                "CSV Files (*.csv)"
            )
            if not file_path:
                return

            try:
                success = self._logic.export.export_to_csv(self._selected_invoice_numbers, file_path)
                if success:
                    show_information_message_box(self._view, "موفقیت",
                                                 f"فاکتورها با موفقیت در فایل '{file_path}' ذخیره شدند.")
                else:
                    show_error_message_box(self._view, "خطا",
                                           "عملیات صادر کردن فاکتورها ناموفق بود.")
            except Exception as e:
                logger.error(f"Error exporting to CSV: {e}")
                show_error_message_box(self._view, "خطا", f"خطا در صادر کردن فایل CSV: {e}")

        show_question_message_box(parent=self._view, title="خروجی اکسل",
                                  message=f"آیا از خروجی اکسل  {count} فاکتور انتخاب شده مطمئن هستید؟",
                                  button_1="بله", button_2="خیر", yes_func=export_to_excel)

    def _toggle_column_filters(self):
        self._is_column_filter_visible = not self._is_column_filter_visible
        self._view.toggle_column_filter_widgets(self._is_column_filter_visible)

    def _set_column_visibility(self, col_index: int, is_visible: bool):
        self._logic.settings.set_column_visibility(col_index, is_visible)
        self._view.set_column_visibility(col_index, is_visible)

    def _load_column_settings(self):
        visibility_states = self._logic.settings.load_column_visibility()
        self._view.restore_column_checkboxes(visibility_states)
        for i, is_visible in enumerate(visibility_states):
            self._set_column_visibility(i, is_visible)

    def _save_column_settings(self):
        self._logic.settings.save_column_visibility()
        logger.info("Column settings saved.")

    def _show_file_dialog(self, title: str, file_filter: str) -> Optional[str]:
        path, _ = QFileDialog.getOpenFileName(self._view, title, "", file_filter)
        return path

    def _show_save_dialog(self, title: str, default_name: str, file_filter: str) -> Optional[str]:
        path, _ = QFileDialog.getSaveFileName(self._view, title, default_name, file_filter)
        return path

    def _show_invoice_summary(self, invoice_number: str):
        """Fetches full invoice details and its history, then displays them."""

        # Fetch invoice, items, AND edit history
        invoice_details = self._logic.invoice.get_invoice_with_details(invoice_number)
        edit_history = self._logic.invoice.get_invoice_edit_history(invoice_number)

        if not invoice_details:
            show_error_message_box(self._view, "خطا", "فاکتور مورد نظر برای نمایش خلاصه یافت نشد.")
            return

        invoice_data, invoice_items = invoice_details

        # Create and show the dialog with all the necessary data
        summary_dialog = InvoiceSummaryDialog(invoice_data, invoice_items, edit_history, self._view)
        summary_dialog.exec()

    def _show_deleted_invoices(self):
        """Fetches all deleted invoices and displays them in a new dialog."""
        try:
            deleted_invoices_data = self._logic.invoice.get_all_deleted_invoices()
            if not deleted_invoices_data:
                show_information_message_box(self._view, "اطلاعات", "هیچ فاکتور حذف شده‌ای یافت نشد.")
                return

            dialog = DeletedInvoicesDialog(deleted_invoices_data, self._view)
            dialog.exec()
        except Exception as e:
            logger.error(f"Error showing deleted invoices: {e}")
            show_error_message_box(self._view, "خطا", f"خطا در نمایش فاکتورهای حذف شده: {e}")

    def _handle_deep_edit_request(self, invoice_number: str):
        """Handles the request for a deep edit by fetching all data and emitting it upwards."""
        invoice_details = self._logic.invoice.get_invoice_with_details(invoice_number)

        if not invoice_details:
            show_error_message_box(self._view, "خطا", "اطلاعات کامل فاکتور برای ویرایش یافت نشد.")
            return

        invoice_data, items_data = invoice_details
        self.request_deep_edit_navigation.emit(invoice_data, items_data)
        print(f"DEBUG: Emitted deep edit request for invoice {invoice_number} to the main controller")
