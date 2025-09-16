# features/Invoice_Page/invoice_preview/invoice_preview_controller.py

from PySide6.QtWidgets import QFileDialog, QMessageBox, QApplication, QWidget
from PySide6.QtGui import QPixmap, QPainter, QPageSize, QRegion
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtCore import QPoint

from typing import Callable

from features.Invoice_Page.invoice_preview.invoice_preview_view import MainInvoicePreviewWidget
from features.Invoice_Page.invoice_preview.invoice_preview_logic import InvoicePreviewLogic
from features.Invoice_Page.invoice_page_state_manager import WorkflowStateManager

from shared import show_warning_message_box, show_information_message_box, show_error_message_box


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

    def _connect_signals(self):
        """Connects signals from the _view to slots in this controller."""
        self._view.print_clicked.connect(self.print_invoice)
        self._view.save_pdf_clicked.connect(self.save_as_pdf)
        self._view.save_png_clicked.connect(self.save_as_png)
        self._view.next_page_clicked.connect(self.next_page)
        self._view.prev_page_clicked.connect(self.prev_page)

    def prepare_and_display_data(self):
        """Assembles the final invoice and updates the _view for the first time."""
        # 1. Get all necessary data from the state manager
        customer = self._state_manager.get_customer()
        details = self._state_manager.get_invoice_details()
        assignments = self._state_manager.get_assignments()

        if not all([customer, details, assignments]):
            print("ERROR: Missing data in state manager.")
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
        items = self._logic.get_items_for_page(self._invoice, self.current_page)
        self._view.update_view(self._invoice, items, self.current_page, self.total_pages)

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
        """Manages the check-confirm-save workflow."""
        if not self._invoice: return

        invoice_number = self._invoice.invoice_number
        existing_path = self._logic.get_invoice_path(invoice_number)

        if existing_path:
            reply = QMessageBox.question(self._view, "تایید ذخیره مجدد",
                                         f"این فاکتور قبلاً ذخیره شده است. آیا می‌خواهید بازنویسی کنید؟",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return

        file_path, _ = QFileDialog.getSaveFileName(self._view, file_dialog_title, f"Invoice-{invoice_number}",
                                                   file_filter)
        if not file_path:
            return

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
        if not self._logic.invoice:
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

    def get_view(self) -> QWidget:
        return self._view
