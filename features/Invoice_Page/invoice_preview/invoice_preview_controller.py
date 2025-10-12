# features/Invoice_Page/invoice_preview/invoice_preview_controller.py

from PySide6.QtWidgets import QFileDialog, QApplication, QDialog
from PySide6.QtGui import QPixmap, QPainter, QPageSize, QRegion
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtCore import QPoint

from typing import Callable, List

from features.Invoice_Page.invoice_preview.invoice_preview_view import MainInvoicePreviewWidget
from features.Invoice_Page.invoice_preview.invoice_preview_logic import InvoicePreviewLogic
from features.Invoice_Page.invoice_page_state_manager import WorkflowStateManager
from features.Invoice_Page.invoice_preview.invoice_preview_settings_dialog import SettingsDialog

from shared import (show_warning_message_box, show_information_message_box, show_error_message_box,
                    show_question_message_box)
from shared.orm_models.invoices_models import EditedInvoiceModel


class InvoicePreviewController:
    """
    Manages the application flow for the preview step, connecting the
    UI (View) with the business _logic (Logic).
    """

    def __init__(self, view: MainInvoicePreviewWidget, logic: InvoicePreviewLogic, state_manager: WorkflowStateManager):
        self._state_manager = state_manager
        self._logic = logic
        self._view = view

        self._invoice = None
        self.current_page = 1
        self.total_pages = 1

        self._connect_signals()

    def get_view(self) -> MainInvoicePreviewWidget:
        """"""
        return self._view

    def _connect_signals(self):
        """Connects signals from the _view to slots in this controller."""
        self._view.print_clicked.connect(self.print_invoice)
        self._view.save_pdf_clicked.connect(self.save_as_pdf)
        self._view.save_png_clicked.connect(self.save_as_png)
        self._view.next_page_clicked.connect(self.next_page)
        self._view.prev_page_clicked.connect(self.prev_page)
        self._view.issue_clicked.connect(self.issue_invoice)
        self._view.settings_clicked.connect(self._on_settings_requested)

    def prepare_and_display_data(self):
        """Assembles the final invoice and updates the _view for the first time."""
        # 1. Get all necessary data from the state manager
        customer = self._state_manager.get_customer()
        details = self._state_manager.get_invoice_details()
        assignments = self._state_manager.get_assignments()

        if not all([customer, details, assignments]):
            show_error_message_box(self._view, "خطای داده", "اطلاعات لازم برای ساخت پیش‌نمایش فاکتور یافت نشد.")
            return

        # 2. Ask the _logic layer to assemble the final Invoice DTO
        self._invoice = self._logic.assemble_invoice_data(customer, details, assignments)

        # 3. Use the _logic layer for pagination calculations
        self.current_page = 1
        self.total_pages = self._logic.get_total_pages(self._invoice)
        self._update_view()

    def _update_view(self):
        """Fetches the correct items for the current page and tells the _view to render."""
        if not self._invoice: return

        settings = self._logic.settings_manager.get_current_settings()
        items = self._logic.get_items_for_page(self._invoice, self.current_page)

        existing_invoice_orm = self._logic.get_issued_invoice(self._invoice.invoice_number)
        is_issued = existing_invoice_orm is not None

        # 2. Call the view's update method
        self._view.update_view(self._invoice, items, self.current_page, self.total_pages, settings)
        self._view.control_panel.issue_button.setEnabled(True)

    def issue_invoice(self):
        """
        Handles the smart invoice issuance workflow.
        - Issues a new invoice normally.
        - For existing invoices, checks for changes and issues a new version if needed.
        """
        if not self._invoice:
            show_error_message_box(self._view, "خطا", "فاکتوری برای صدور وجود ندارد.")
            return

        original_invoice_data = self._state_manager.get_original_invoice_for_edit()
        is_edit_mode = original_invoice_data is not None

        if not is_edit_mode:
            # --- STANDARD WORKFLOW for a new invoice ---
            self._confirm_and_issue_new()
        else:
            # --- EDITING WORKFLOW for an existing invoice ---
            self._handle_reissue()

    def _confirm_and_issue_new(self):
        """Handles the simple case of issuing a brand-new invoice."""
        def do_issue():
            assignments = self._state_manager.get_assignments()
            success, message = self._logic.issue_invoice_in_database(self._invoice, assignments)
            if success:
                show_information_message_box(self._view, "موفق", message)
                self._update_view() # Refresh view to reflect issued state
            else:
                show_error_message_box(self._view, "خطا", message)

        title = "تایید صدور فاکتور"
        message = f"آیا از صدور و ثبت نهایی فاکتور شماره {self._invoice.invoice_number} اطمینان دارید؟"
        show_question_message_box(parent=self._view, title=title, message=message,
                                  button_1="بله",button_2="خیر", yes_func=do_issue)

    def _handle_reissue(self):
        """
        Handles the logic for re-issuing an edited invoice using a single,
        session-safe call to the logic layer.
        """
        import re
        base_invoice_number = re.split(r'-v\d+', self._invoice.invoice_number)[0]
        assignments = self._state_manager.get_assignments()
        new_items = [item for sublist in assignments.values() for item in sublist]

        # --- MODIFICATION START ---
        # 1. Make a single call to the logic layer
        has_changed, edit_logs = self._logic.prepare_reissue_data(
            base_invoice_number, self._invoice, new_items
        )

        # 2. Check the result
        if not has_changed:
            show_warning_message_box(self._view, "بدون تغییر",
                                     "اطلاعات فاکتور تغییری نکرده است. فاکتور جدیدی صادر نشد.")
            return

        # 3. If there are changes, the 'do_reissue' function now receives the pre-generated logs
        def do_reissue(generated_logs: List[EditedInvoiceModel]):
            new_versioned_number = self._logic.get_next_invoice_version_number(base_invoice_number)
            self._invoice.invoice_number = new_versioned_number
            edit_remark = f"* نسخه ویرایش شده فاکتور شماره {base_invoice_number}"
            self._invoice.remarks = f"{edit_remark}\n{self._invoice.remarks}".strip()

            # Pass the generated logs directly to the database saving method
            success, message = self._logic.issue_invoice_in_database(self._invoice, assignments, generated_logs)

            if success:
                show_information_message_box(self._view, "موفق",
                                             f"تغییرات شناسایی و ثبت شد. نسخه جدید فاکتور با شماره {new_versioned_number} صادر شد.")
                self._update_view()
            else:
                show_error_message_box(self._view, "خطا", message)

        title = "تایید صدور نسخه جدید"
        message = "تغییراتی در فاکتور شناسایی شد. آیا مایل به صدور یک نسخه جدید و ویرایش شده هستید؟"

        # 4. The lambda now passes the safe 'edit_logs' list, not the detached ORM object
        show_question_message_box(parent=self._view, title=title, message=message, button_1="بله، صادر کن",
                                  button_2="خیر", yes_func=lambda: do_reissue(edit_logs))

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._update_view()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._update_view()

    def save_as_pdf(self):
        """Orchestrates saving the invoice as a PDF."""
        if not self._invoice:
            show_error_message_box(self._view,
                                   "خطا",
                                   "فاکتوری برای ذخیره وجود ندارد. لطفاً مراحل قبل را تکمیل کنید.")
            return

        self._handle_save_operation(
            save_logic_func=self._save_to_pdf_file,
            file_dialog_title="ذخیره به صورت PDF",
            file_filter="PDF Files (*.pdf)"
        )

    def save_as_png(self):
        """Orchestrates saving the invoice as a PNG."""
        if not self._invoice:
            show_error_message_box(self._view,
                                   "خطا",
                                   "فاکتوری برای ذخیره وجود ندارد. لطفاً مراحل قبل را تکمیل کنید.")
            return

        if self.total_pages > 1:
            show_warning_message_box(self._view, "عملیات نامعتبر",
                                     "فاکتورهای چندصفحه‌ای را نمی‌توان با فرمت PNG ذخیره کرد.")
            return

        self._handle_save_operation(
            save_logic_func=self._save_to_png_file,
            file_dialog_title="ذخیره به صورت PNG",
            file_filter="PNG Files (*.png)"
        )

    def _handle_save_operation(self, save_logic_func: Callable[[str], bool], file_dialog_title: str, file_filter: str):
        """
        Manages the check-confirm-save workflow. Checks if a file already exists
        and acts accordingly.
        """
        if not self._invoice:
            return

        invoice_number = self._invoice.invoice_number
        existing_path = self._logic.get_invoice_path(invoice_number)

        if existing_path:
            # Case 1: The invoice was saved before. Ask to overwrite.
            def save_anyway():
                self._prompt_and_save(save_logic_func, file_dialog_title, file_filter)

            title = "تایید ذخیره مجدد"
            message = f"این فاکتور قبلاً ذخیره شده است. آیا می‌خواهید بازنویسی کنید؟"
            show_question_message_box(parent=self._view, title=title, message=message,
                                      button_1="بله", button_2="خیر",
                                      yes_func=save_anyway)
        else:
            # Case 2: The invoice has never been saved. Prompt to save directly.
            self._prompt_and_save(save_logic_func, file_dialog_title, file_filter)

    def _prompt_and_save(self, save_logic_func: Callable[[str], bool], file_dialog_title: str, file_filter: str):
        """
        Handles the core logic: showing the file dialog, saving the file, updating the DB,
        and providing user feedback.
        """
        invoice_number = self._invoice.invoice_number
        default_path = f"Invoice-{invoice_number}"
        file_path, _ = QFileDialog.getSaveFileName(self._view, file_dialog_title, default_path, file_filter)

        # If user cancels the dialog, file_path will be empty
        if not file_path:
            return

        # Call the appropriate save function (PDF or PNG)
        if save_logic_func(file_path):
            if self._logic.update_invoice_path(invoice_number, file_path):
                show_information_message_box(self._view, "موفق", f"فاکتور با موفقیت ذخیره شد:\n{file_path}")
            else:
                show_warning_message_box(self._view, "خطای پایگاه داده",
                                         "فاکتور ذخیره شد، اما مسیر آن در پایگاه داده ثبت نشد.")
        else:
            show_error_message_box(self._view, "خطا", "خطا در ذخیره سازی فایل.")

    def _save_to_pdf_file(self, file_path: str) -> bool:
        """Renders the entire document to a PDF file."""
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(file_path)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setResolution(300)
        return self._render_document(printer)

    def _save_to_png_file(self, file_path: str) -> bool:
        """Renders the currently visible page to a PNG file."""
        widget_to_render = self._view.get_invoice_widget_for_render()
        pixmap = QPixmap(widget_to_render.size())
        widget_to_render.render(pixmap)
        return pixmap.save(file_path, "PNG")

    def print_invoice(self):
        """Opens a print dialog and prints the document."""
        if not self._invoice:
            show_error_message_box(self._view, "خطا", "فاکتوری برای چاپ وجود ندارد.")
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        print_dialog = QPrintDialog(printer, self._view)  # Corrected self._view -> self._view
        if print_dialog.exec() == QPrintDialog.DialogCode.Accepted:
            if not self._render_document(printer):
                show_error_message_box(self._view, "خطا", "خطا در فرآیند چاپ.")

    def _render_document(self, printer: QPrinter) -> bool:
        """Renders all pages of the document to a QPrinter device (PDF or physical)."""
        painter = QPainter()
        if not painter.begin(printer):
            return False

        original_page = self.current_page
        try:
            for page in range(1, self.total_pages + 1):
                self.current_page = page
                self._update_view()
                QApplication.processEvents()  # Allow UI to update before rendering

                widget_to_render = self._view.get_invoice_widget_for_render()
                page_rect = printer.pageRect(QPrinter.DevicePixel)
                scale = min(page_rect.width() / widget_to_render.width(),
                            page_rect.height() / widget_to_render.height())

                painter.save()
                painter.scale(scale, scale)
                widget_to_render.render(painter, QPoint(0, 0), QRegion(widget_to_render.rect()))
                painter.restore()

                if page < self.total_pages:
                    printer.newPage()
        except Exception as e:
            print(f"Error during rendering: {e}")
            return False
        finally:
            painter.end()
            self.current_page = original_page  # Restore original state
            self._update_view()
        return True

    def _on_settings_requested(self):
        """Opens the settings dialog and applies changes if accepted."""
        # Get current settings to populate the dialog
        current_settings = self._logic.settings_manager.get_current_settings()

        dialog = SettingsDialog(current_settings, self._view)

        if dialog.exec() == QDialog.Accepted:
            # Get new settings from the dialog
            new_settings = dialog.get_new_settings()

            # Tell the logic's manager to save them
            self._logic.settings_manager.save_settings(new_settings)

            # Immediately trigger a refresh of the view to apply the new settings
            print("Settings updated. Refreshing view.")
            self._update_view()

    def reset_view(self):
        """Resets the invoice preview view to its default empty state."""
        empty_invoice = self._logic.create_empty_preview()

        items_on_page = []
        current_page = 1
        total_pages = 1
        settings = {}

        self._view.update_view(empty_invoice, items_on_page, current_page, total_pages, settings)
        # Optionally clear static UI fields if they are outside update_view()
        if hasattr(self, "customer_name"):
            self.customer_name.setText("نامشخص")

        # Disable export/print buttons since there's no invoice
        self._view.control_panel.export_button.setEnabled(False)
        self._view.control_panel.issue_button.setEnabled(False)
        self._view.control_panel.prev_button.setEnabled(False)
        self._view.control_panel.next_button.setEnabled(False)

        print("VIEW RESET: Invoice preview cleared to default state.")
