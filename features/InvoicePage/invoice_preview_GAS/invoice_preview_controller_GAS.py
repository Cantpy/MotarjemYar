# controller.py

from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtGui import QPixmap, QPainter, QPageSize
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtCore import QPoint

from features.InvoicePage.invoice_preview_GAS.invoice_preview_view_GAS import MainInvoiceWindow
from features.InvoicePage.invoice_preview_GAS.invoice_preview_logic_GAS import InvoiceService, create_mock_invoice
from features.InvoicePage.invoice_preview_GAS.invoice_preview_repo_GAS import InvoiceRepository


class InvoiceController:
    """
    Manages the application flow, connecting the UI (View) with the business logic (Service).
    """

    def __init__(self, view: MainInvoiceWindow):
        self.view = view
        self.invoice_data = create_mock_invoice()
        self.service = InvoiceService(self.invoice_data)

        self.current_page = 1
        self.total_pages = self.service.get_total_pages()

        self._connect_signals()
        self.update_view()

    def _connect_signals(self):
        """Connects UI element signals to controller methods."""
        self.view.action_panel.print_button.clicked.connect(self.print_invoice)
        self.view.action_panel.save_pdf_button.clicked.connect(self.save_as_pdf)
        self.view.action_panel.save_png_button.clicked.connect(self.save_as_png)
        self.view.pagination_panel.next_button.clicked.connect(self.next_page)
        self.view.pagination_panel.prev_button.clicked.connect(self.prev_page)

    def update_view(self):
        """
        Updates the invoice preview, now passing the pagination config to the view.
        """
        items = self.service.get_items_for_page(self.current_page)

        # Get the config from the service
        pagination_config = self.service.pagination_config

        # Pass the config to the view's update method
        self.view.invoice_preview.update_content(
            self.invoice_data,
            items,
            self.current_page,
            self.total_pages,
            pagination_config  # Pass the config dictionary
        )

        # Update external pagination controls
        self.view.pagination_panel.prev_button.setEnabled(self.current_page > 1)
        self.view.pagination_panel.next_button.setEnabled(self.current_page < self.total_pages)

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.update_view()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.update_view()

    def save_as_png(self):
        """Saves the current view of the invoice as a PNG image."""
        file_path, _ = QFileDialog.getSaveFileName(self.view, "ذخیره به صورت PNG", "", "PNG Files (*.png)")
        if not file_path:
            return

        widget_to_render = self.view.get_invoice_widget()
        pixmap = QPixmap(widget_to_render.size())
        widget_to_render.render(pixmap)

        if pixmap.save(file_path, "PNG"):
            QMessageBox.information(self.view, "موفق", f"فاکتور با موفقیت در مسیر زیر ذخیره شد:\n{file_path}")
        else:
            QMessageBox.critical(self.view, "خطا", "خطا در ذخیره سازی تصویر.")

    def save_as_pdf(self):
        """Saves the entire multi-page invoice as a PDF file."""
        file_path, _ = QFileDialog.getSaveFileName(self.view, "ذخیره به صورت PDF", "", "PDF Files (*.pdf)")
        if not file_path:
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(file_path)

        # BUG FIX: Use QPageSize for setting the page size in PySide6
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))

        self._render_document(printer)
        QMessageBox.information(self.view, "موفق", f"فاکتور با موفقیت در مسیر زیر ذخیره شد:\n{file_path}")

    def print_invoice(self):
        """Opens a print dialog and prints the entire multi-page invoice."""
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        print_dialog = QPrintDialog(printer, self.view)

        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))

        if print_dialog.exec() == QPrintDialog.DialogCode.Accepted:
            self._render_document(printer)

    def _render_document(self, printer_or_pdf_writer):
        """A generic method to render the document page by page to a QPrinter object."""
        painter = QPainter()
        if not painter.begin(printer_or_pdf_writer):
            QMessageBox.critical(self.view, "خطا", "امکان شروع عملیات چاپ وجود ندارد.")
            return

        original_page = self.current_page

        for page in range(1, self.total_pages + 1):
            self.current_page = page
            self.update_view()

            # Render the widget to the painter
            self.view.get_invoice_widget().render(painter)

            # Add a new page if it's not the last one
            if page < self.total_pages:
                printer_or_pdf_writer.newPage()

        painter.end()

        # Restore the view to its original state
        self.current_page = original_page
        self.update_view()
