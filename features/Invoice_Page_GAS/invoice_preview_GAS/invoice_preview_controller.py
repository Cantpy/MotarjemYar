# controller.py

from PySide6.QtWidgets import QFileDialog, QMessageBox, QApplication
from PySide6.QtGui import QPixmap, QPainter, QPageSize, QRegion
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtCore import QPoint

from typing import Callable
from datetime import date

from features.Invoice_Page_GAS.invoice_preview_GAS.invoice_preview_view import MainInvoiceWindow
from features.Invoice_Page_GAS.invoice_preview_GAS.invoice_preview_logic import InvoiceService, create_mock_invoice
from features.Invoice_Page_GAS.invoice_preview_GAS.invoice_preview_repo import InvoiceRepository
from features.Invoice_Page_GAS.invoice_preview_GAS.invoice_preview_models import Invoice, Customer, InvoiceItem

from shared import show_warning_message_box, show_information_message_box, show_error_message_box


class InvoiceController:
    """
    Manages the application flow, connecting the UI (View) with the business logic (Service).
    """

    def __init__(self, view: MainInvoiceWindow):
        self.view = view
        self.invoice_data = create_mock_invoice()
        self.service = InvoiceService(self.invoice_data)
        self.repo = InvoiceRepository()

        self.current_page = 1
        self.total_pages = self.service.get_total_pages()

        self._connect_signals()
        self.update_view()

    def _connect_signals(self):
        self.view.action_panel.print_button.clicked.connect(self.print_invoice)
        self.view.action_panel.save_pdf_button.clicked.connect(self.save_as_pdf)
        self.view.action_panel.save_png_button.clicked.connect(self.save_as_png)
        self.view.pagination_panel.next_button.clicked.connect(self.next_page)
        self.view.pagination_panel.prev_button.clicked.connect(self.prev_page)

    def load_new_invoice(self, builder_data: 'InvoiceBuilder'):
        """
        This is the new public method called by the main window to load final data.
        It rebuilds the entire invoice model from the builder object.
        """
        # --- Step 1: Extract Customer and Office Info ---
        customer_dict = builder_data.customer_data.get('customer', {})
        new_customer = Customer(
            name=customer_dict.get('name', 'نامشخص'),
            national_id=customer_dict.get('national_id', 'نامشخص'),
            phone=customer_dict.get('phone', 'نامشخص'),
            address=customer_dict.get('address', '')
        )

        # NOTE: Office info is likely static. If it comes from the details page,
        # you would extract it from builder_data.invoice_details['office_info']
        office_info = self.invoice_data.office  # Keep the existing office info for now

        # --- Step 2: Extract Document Items ---
        new_items = []
        for item_dict in builder_data.document_items:
            new_items.append(
                InvoiceItem(
                    name=item_dict.get('name', ''),
                    type=item_dict.get('type', ''),
                    quantity=item_dict.get('count', 1),
                    judiciary_seal=item_dict.get('judiciary_display', '-'),
                    foreign_affairs_seal=item_dict.get('foreign_affairs_display', '-'),
                    total_price=item_dict.get('total_price', 0.0)
                )
            )

        # --- Step 3: Extract Invoice Details and Financials ---
        details_dict = builder_data.invoice_details
        subtotal = sum(item.total_price for item in new_items)

        # --- Step 4: Rebuild the main Invoice object ---
        self.invoice_data = Invoice(
            invoice_number=details_dict.get('receipt_number', 'پیش‌نویس'),
            issue_date=details_dict.get('issue_date', date.today()),  # You'll need to parse this
            delivery_date=details_dict.get('delivery_date', date.today()),  # You'll need to parse this
            username=details_dict.get('username', ''),
            customer=new_customer,
            office=office_info,
            source_language=details_dict.get('source_language', ''),
            target_language=details_dict.get('target_language', ''),
            items=new_items,
            total_amount=subtotal,
            discount_amount=details_dict.get('discount_amount', 0.0),
            advance_payment=details_dict.get('advance_payment_amount', 0.0),
            emergency_cost=details_dict.get('emergency_cost', 0.0),
            remarks=details_dict.get('remarks', '')
        )
        # Note: You will need to parse the date strings from the details dictionary
        # into actual date objects for the Invoice dataclass.

        # --- Step 5: Update the service and refresh the view ---
        self.service = InvoiceService(self.invoice_data)
        self.current_page = 1
        self.total_pages = self.service.get_total_pages()
        self.update_view()  # This will refresh the UI with the complete invoice

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

    def save_as_pdf(self):
        """Orchestrates saving the invoice as a PDF."""
        self._handle_save_operation(
            save_logic_func=self._save_to_pdf_file,
            file_dialog_title="ذخیره به صورت PDF",
            file_filter="PDF Files (*.pdf)"
        )

    def save_as_png(self):
        """Orchestrates saving the invoice as a PNG."""
        if self.total_pages > 1:
            show_warning_message_box(
                self.view,
                "عملیات نامعتبر",
                "فاکتورهای چندصفحه‌ای را نمی‌توان با فرمت PNG ذخیره کرد.\n"
                "این عمل فقط صفحه اول را ذخیره می‌کند. برای ذخیره تمام صفحات، لطفاً از گزینه 'ذخیره PDF' استفاده نمایید."
            )
            return

        self._handle_save_operation(
            save_logic_func=self._save_to_png_file,
            file_dialog_title="ذخیره به صورت PNG",
            file_filter="PNG Files (*.png)"
        )

    def _handle_save_operation(self, save_logic_func: Callable[[str], bool], file_dialog_title: str, file_filter: str):
        """
        Manages the check-confirm-save workflow.
        """
        invoice_number = self.invoice_data.invoice_number

        # 1. Check for existing path in the database
        existing_path = self.repo.get_invoice_path(invoice_number)

        # 2. If path exists, ask for confirmation
        if existing_path:
            reply = QMessageBox.question(
                self.view,
                "تایید ذخیره مجدد",
                f"این فاکتور قبلاً در مسیر زیر ذخیره شده است:\n\n{existing_path}\n\nآیا می‌خواهید دوباره آن را ذخیره کرده و مسیر جدید را جایگزین نمایید؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return  # Abort the operation

        # 3. Show file save dialog to get the new path
        file_path, _ = QFileDialog.getSaveFileName(self.view, file_dialog_title, "", file_filter)
        if not file_path:
            return  # User cancelled the dialog

        # 4. Execute the actual save logic (for PDF or PNG)
        if save_logic_func(file_path):
            # 5. If save was successful, update the path in the database
            if self.repo.update_invoice_path(invoice_number, file_path):
                show_information_message_box(self.view, "موفق",
                                             f"فاکتور با موفقیت ذخیره و مسیر آن در پایگاه داده به‌روزرسانی شد:\n{file_path}")
            else:
                show_warning_message_box(self.view, "خطای پایگاه داده",
                                         "فاکتور ذخیره شد، اما در به‌روزرسانی مسیر آن در پایگاه داده خطایی رخ داد.")
        else:
            show_error_message_box(self.view, "خطا", f"خطا در ذخیره سازی فایل در مسیر:\n{file_path}")

    def _save_to_pdf_file(self, file_path: str) -> bool:
        """Contains the specific logic to render and save a PDF."""
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(file_path)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setResolution(300)
        printer.setFullPage(True)
        return self._render_document(printer)

    def _save_to_png_file(self, file_path: str) -> bool:
        """Contains the specific logic to render and save a PNG."""
        widget_to_render = self.view.get_invoice_widget()
        pixmap = QPixmap(widget_to_render.size())
        widget_to_render.render(pixmap)
        return pixmap.save(file_path, "PNG")

    def print_invoice(self):
        """Opens a print dialog and prints the entire multi-page invoice."""
        printer = QPrinter(QPrinter.HighResolution)
        print_dialog = QPrintDialog(printer, self.view)

        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setResolution(300)

        if print_dialog.exec() == QPrintDialog.Accepted:
            if not self._render_document(printer):
                show_error_message_box(self.view, "خطا", "خطا در فرآیند چاپ.")

    def _render_document(self, printer: QPrinter) -> bool:
        """
        Definitive Version: Renders the document with both correct scaling
        and the proper QWidget.render() method signature.
        """
        painter = QPainter()
        if not painter.begin(printer):
            return False

        original_page = self.current_page

        try:
            for page in range(1, self.total_pages + 1):
                self.current_page = page
                self.update_view()

                QApplication.processEvents()

                widget_to_render = self.view.get_invoice_widget()

                # --- Scaling Logic ---
                page_rect_pixels = printer.pageRect(QPrinter.DevicePixel)
                pdf_width = page_rect_pixels.width()
                pdf_height = page_rect_pixels.height()

                widget_rect = widget_to_render.rect()
                widget_width = widget_rect.width()
                widget_height = widget_rect.height()

                scale_x = pdf_width / widget_width
                scale_y = pdf_height / widget_height
                scale = min(scale_x, scale_y)

                painter.resetTransform()
                painter.scale(scale, scale)
                # --- End Scaling Logic ---

                # --- FIX: Call render with the correct, full signature ---
                target_point = QPoint(0, 0)
                # We render the entire widget's area
                source_region = QRegion(widget_to_render.rect())

                widget_to_render.render(painter, target_point, source_region)

                if page < self.total_pages:
                    printer.newPage()

        except Exception as e:
            print(f"Error during rendering: {e}")
            return False
        finally:
            painter.end()
            self.current_page = original_page
            self.update_view()

        return True
