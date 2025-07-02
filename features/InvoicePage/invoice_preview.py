import sqlite3
import os
import re
from PySide6.QtCore import Qt, QSettings, QPoint
from PySide6.QtWidgets import (QDialog, QTableWidget, QHeaderView, QSizePolicy, QMessageBox, QFileDialog,
                               QTableWidgetItem, QInputDialog, QWidget, QAbstractItemView, QApplication)
from PySide6.QtGui import QPainter, QRegion, QFont, QTextCharFormat, QTextCursor, QPageSize
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from modules.helper_functions import to_persian_number, return_resource, get_persian_date, persian_to_english_number
from modules.InvoicePage.helper_function import clear_table_selection, block_column_zero_selection
from contextlib import contextmanager
import json
from collections import namedtuple
from modules.user_context import UserContext


USERS_DATABASE = return_resource('databases', 'users.db')
INVOICES_DATABASE = return_resource('databases', 'invoices.db')
STYLES_ABSOLUTE_PATH = return_resource("styles", "invoice_preview_style.qss")


InvoiceSummary = namedtuple('InvoiceSummary', [
    'total_official_docs_count',
    'total_unofficial_docs_count',
    'total_pages_count',
    'total_judiciary_count',
    'total_foreign_affairs_count',
    'total_additional_doc_count',
    'total_translation_price'
])

class InvoicePreview(QDialog):
    """
    A dialog for previewing invoices with pagination support,
    database integration, and user management.
    """

    # Scale factor configurations
    SCALE_CONFIGS = {
        "125%": {
            'ui_module': 'qt_designer_ui.ui_paginated_invoice_widget_large',
            'column_width': [4, 300, 90, 50, 50, 50, 130],
            'first_page_rows': 17,
            'last_page_rows': 16,
            'first_table_rows': 10,
            'other_page_rows': 26,
            'remarks_font': 10,
            'scale_factor': 1.0
        },
        "100%": {
            'ui_module': 'qt_designer_ui.ui_paginated_invoice_widget_medium',
            'column_width': [3, 230, 50, 30, 30, 30, 70],
            'first_page_rows': 14,
            'last_page_rows': 9,
            'first_table_rows': 6,
            'other_page_rows': 21,
            'remarks_font': 9,
            'scale_factor': 0.75
        },
        "75%": {
            'ui_module': 'qt_designer_ui.ui_paginated_invoice_widget_small',
            'column_width': [2, 190, 35, 20, 20, 20, 50],
            'first_page_rows': 11,
            'last_page_rows': 8,
            'first_table_rows': 5,
            'other_page_rows': 17,
            'remarks_font': 7.5,
            'scale_factor': 0.5
        }
    }

    def __init__(self, parent_invoice_widget, app_settings):  # user_context: UserContext
        super().__init__()

        # Initialize core attributes
        self.parent_invoice_page = parent_invoice_widget
        # self.user_context = user_context
        self.app_settings = app_settings
        self.current_page = 1
        self.total_rows = 0
        self.all_table_data = []
        self.advance_payment = 0
        self.discount_amount = 0
        self.original_geometry = None
        self.original_sizes = {}

        # Initialize UI and settings
        self._load_scale_settings()
        self._setup_ui()
        self._apply_styles()
        self._configure_window()
        self._initialize_data()
        self._setup_connections()
        self._configure_table()
        self._setup_language_settings()

        # Set invoice data and labels
        self._extract_invoice_data()
        self._set_labels()
        self._load_remarks()
        self.set_text_edit_font_size()

    def _load_scale_settings(self):
        """Load scale settings and configure UI parameters."""
        self.settings = QSettings("MyScale", "MyPreview")
        saved_scale = self.settings.value("scaling_factor", "100%")

        # Get configuration for the saved scale, fallback to 100%
        config = self.SCALE_CONFIGS.get(saved_scale, self.SCALE_CONFIGS["100%"])

        # Import the appropriate UI module
        ui_module = __import__(config['ui_module'], fromlist=['Ui_MainLayout'])
        Ui_MainLayout = ui_module.Ui_MainLayout

        # Set configuration attributes
        for key, value in config.items():
            if key != 'ui_module':
                setattr(self, key, value)

        # Load UI
        self.ui = Ui_MainLayout()
        self.ui.setupUi(self)

    def _setup_ui(self):
        """Setup basic UI configuration."""
        self.original_geometry = self.geometry()

        # Save original widget sizes
        for widget in self.findChildren(QWidget):
            self.original_sizes[widget] = widget.size()

    def _apply_styles(self):
        """Apply custom stylesheet."""
        try:
            with open(STYLES_ABSOLUTE_PATH, "r") as style_file:
                stylesheet = style_file.read()
                self.setStyleSheet(stylesheet)
        except FileNotFoundError:
            print(f"Warning: Style file not found at {STYLES_ABSOLUTE_PATH}")

    def _configure_window(self):
        """Configure window properties."""
        self.setWindowTitle("پیش‌نمایش فاکتور")
        self.setFixedSize(self.size())
        self.ui.pages_gb.hide()

    def _initialize_data(self):
        """Initialize invoice data and pagination."""
        self.extract_data_from_invoice_table()
        self.update_pages()
        self.populate_table()

    def _setup_connections(self):
        """Setup signal connections for all buttons."""
        button_connections = {
            self.ui.print_invoice_button: self.print_form,
            self.ui.save_invoice_button: self.save_invoice,
            self.ui.delivery_date_button: self.open_calendar_dialog,
            self.ui.send_email_button: self.open_send_dialog,
            self.ui.translation_languages_button: self.open_language_dialog,
            self.ui.next_page_button: self.next_page,
            self.ui.previous_page_button: self.previous_page,
            self.ui.discount_button: self.apply_discount,
            self.ui.advance_payment_button: self.get_advance_payment,
            self.ui.attention_button: self.open_remarks_dialog
        }

        for button, slot in button_connections.items():
            button.clicked.connect(slot)

    def _configure_table(self):
        """Configure table widget properties."""
        # Size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ui.tableWidget1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Header configuration
        self.ui.tableWidget1.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ui.tableWidget1.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.tableWidget1.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Block column zero selection
        block_column_zero_selection(self.ui.tableWidget1)

    def _setup_language_settings(self):
        """Setup default language settings."""
        self.language_settings = QSettings("YourCompany", "YourApp")
        self.set_default_language()

    def _extract_invoice_data(self):
        """Extract invoice data from parent widget."""
        self.invoice_no = self.parent_invoice_page.get_current_invoice_no()
        self.customer_name = self.parent_invoice_page.ui.full_name_le.text()
        self.national_id = self.parent_invoice_page.ui.national_id_le.text()
        self.phone_no = self.parent_invoice_page.ui.phone_le.text()
        self.issue_date = get_persian_date()
        self.delivery_date = self.ui.delivery_date_label.text()
        self.invoice_price = self.sum_column_values(self.ui.tableWidget1, 6)
        self.file_path = ""

    def set_current_user_label(self):
        """Set the username label with the current user's full name."""
        # current_user_full_name = self.user_context.full_name
        # self.ui.username_label.setText(current_user_full_name)
        pass

    # Table and Data Methods
    def extract_data_from_invoice_table(self):
        """Extract data from the parent invoice table."""
        source_table = self.parent_invoice_page.ui.tableWidget
        row_count = source_table.rowCount()
        column_count = source_table.columnCount()

        extracted_data = []
        for row in range(row_count):
            row_data = []
            for column in range(column_count):
                item = source_table.item(row, column)
                row_data.append(item.text() if item else "")
            extracted_data.append(row_data)

        self.all_table_data = extracted_data
        return extracted_data

    def create_customized_vertical_header(self):
        """Create customized vertical header for the table."""
        if (self.ui.tableWidget1.columnCount() > 0 and
                self.ui.tableWidget1.horizontalHeaderItem(0) and
                self.ui.tableWidget1.horizontalHeaderItem(0).text() == ""):
            return

        self.ui.tableWidget1.verticalHeader().setVisible(False)
        self.ui.tableWidget1.insertColumn(0)
        self.ui.tableWidget1.setHorizontalHeaderItem(0, QTableWidgetItem(""))
        self.ui.tableWidget1.setColumnWidth(0, 5)
        self.ui.tableWidget1.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.tableWidget1.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.ui.tableWidget1.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

    def align_table_content(self):
        """Align table contents (center except for second column)."""
        row_count = self.ui.tableWidget1.rowCount()
        column_count = self.ui.tableWidget1.columnCount()

        for row in range(row_count):
            for col in range(column_count):
                item = self.ui.tableWidget1.item(row, col)
                if item is not None:
                    if col == 1:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    else:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def calculate_total_pages(self):
        """Calculate total number of pages needed for the invoice."""
        self.total_rows = len(self.all_table_data)

        if self.total_rows <= self.first_table_rows:
            return 1
        elif self.first_table_rows < self.total_rows <= self.first_page_rows:
            return 2
        elif self.total_rows <= self.first_page_rows + self.last_page_rows:
            return 2
        else:
            remaining_rows = self.total_rows - self.first_page_rows
            middle_pages = remaining_rows // self.other_page_rows
            last_page_rows = remaining_rows % self.other_page_rows

            if last_page_rows > self.last_page_rows:
                middle_pages += 1

            return 2 + middle_pages

    def populate_table(self):
        """Populate table with data for current page."""
        self.total_rows = len(self.all_table_data)
        total_pages = self.calculate_total_pages()

        # Determine row range for current page
        if self.current_page == 1:
            start_index, end_index = 0, min(self.total_rows, self.first_page_rows)
        elif self.current_page == total_pages:
            start_index = self.first_page_rows + (self.current_page - 2) * self.other_page_rows
            end_index = self.total_rows

            if start_index >= self.total_rows:
                self.ui.tableWidget1.clearContents()
                self.ui.tableWidget1.setRowCount(0)
                self.ui.price_sign_frame.setVisible(True)
                return
        else:
            start_index = self.first_page_rows + (self.current_page - 2) * self.other_page_rows
            end_index = min(start_index + self.other_page_rows, self.total_rows)

        # Populate table
        self.ui.tableWidget1.clearContents()
        self.ui.tableWidget1.setRowCount(end_index - start_index)

        for row_idx, row in enumerate(range(start_index, end_index)):
            absolute_row_number = start_index + row_idx + 1
            self.ui.tableWidget1.setItem(row_idx, 0,
                                         QTableWidgetItem(to_persian_number(absolute_row_number)))

            for col_idx, col_value in enumerate(self.all_table_data[row]):
                self.ui.tableWidget1.setItem(row_idx, col_idx + 1,
                                             QTableWidgetItem(to_persian_number(col_value)))

        if self.current_page == total_pages:
            self.ui.price_sign_frame.setVisible(True)

    def update_pages(self):
        """Update page display based on current page and data."""
        total_pages = self.calculate_total_pages()
        self.ui.pages_gb.setVisible(total_pages > 1)
        self.ui.header_frame.setVisible(self.current_page == 1)
        self.ui.groupBox_6.setVisible(self.current_page == 1)
        self.ui.price_sign_frame.setVisible(self.current_page == total_pages)

        self.populate_table()
        self.create_customized_vertical_header()
        self.align_table_content()
        self.ui.page_label.setText(
            f"صفحه {to_persian_number(self.current_page)} از {to_persian_number(total_pages)}"
        )

    # Navigation Methods
    def next_page(self):
        """Navigate to next page."""
        if self.current_page < self.calculate_total_pages():
            self.current_page += 1
            self.update_pages()

    def previous_page(self):
        """Navigate to previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            self.update_pages()

    # UI Methods
    def set_text_edit_font_size(self):
        """Set font size for text edit widget."""
        if self.ui.textEdit.toPlainText().strip():
            return

        font = QFont()
        font.setPointSize(self.remarks_font)
        self.ui.textEdit.setFont(font)

        char_format = QTextCharFormat()
        char_format.setFont(font)

        cursor = self.ui.textEdit.textCursor()
        cursor.select(QTextCursor.Document)
        cursor.mergeCharFormat(char_format)
        cursor.movePosition(QTextCursor.End)
        self.ui.textEdit.setTextCursor(cursor)

    def set_default_language(self):
        """Set default language for the invoice."""
        default_lang = self.language_settings.value("default_language", type=str)
        language_text = default_lang if default_lang else "انگلیسی"
        self.ui.translation_languges_label.setText(language_text)

    def _set_labels(self):
        """Set all labels with invoice data."""
        # Set user label
        self.set_current_user_label()

        # Set invoice labels
        self.ui.customer_name_label.setText(self.customer_name)
        self.ui.customer_phone_label.setText(to_persian_number(self.phone_no))
        self.ui.receive_date_lable.setText(to_persian_number(self.issue_date))
        self.ui.receipt_no_label.setText(to_persian_number(self.invoice_no))
        self.ui.translation_office_label.setText("دارالترجمه زارعی")
        self.ui.tro_phone_text.setText("شماره تماس: " + to_persian_number("03136691379"))
        self.ui.tro_email_text.setText("ایمیل: " + "translator663@gmail.com")
        self.ui.tro_address_text.setText("آدرس: " + "اصفهان، خ هزار جریب، حد فاصل کوچه هشتم و دهم، ساختمان ۱۱۶")
        self.ui.registration_no_label.setText("شماره ثبت: ۶۶۳")
        self.ui.national_id_label.setText(self.national_id)

        formatted_price = f"{self.invoice_price:,}"
        persian_price = to_persian_number(formatted_price)
        self.ui.total_invoice_amount_label.setText(f"{persian_price} تومان")
        self.ui.total_payable_amount_label.setText(f"{persian_price} تومان")

    # Calculation Methods
    def sum_column_values(self, table_widget: QTableWidget, column_index: int) -> int:
        """Calculate sum of numeric values in a specific column."""
        total = 0
        row_count = table_widget.rowCount()

        for row in range(row_count):
            item = table_widget.item(row, column_index)
            if item and item.text().strip():
                try:
                    value = int(item.text().replace(",", ""))
                    total += value
                except ValueError:
                    continue
            else:
                QMessageBox.warning(self, "خطا", "قیمت فاکتور وارد نشده است!")

        return total

    def update_payable_amount(self):
        """Update total payable amount after discounts and advance payments."""
        try:
            # Extract total amount
            total_text = self.ui.total_invoice_amount_label.text().replace("تومان", "").strip()
            total_text = persian_to_english_number(total_text)
            total_text = re.sub(r"[^\d]", "", total_text)
            total_amount = int(total_text)

            # Calculate final amount
            advance_payment = int(getattr(self, "advance_payment", 0) or 0)
            discount_amount = int(getattr(self, "discount_amount", 0) or 0)
            final_amount = max(0, total_amount - advance_payment - discount_amount)

            # Update UI
            formatted_final = f"{final_amount:,}"
            self.ui.total_payable_amount_label.setText(f"{to_persian_number(formatted_final)} تومان")

        except ValueError as e:
            QMessageBox.warning(self, "خطا", f"خطا در محاسبه: {e}")

    # Payment Methods
    def get_advance_payment(self):
        """Handle advance payment input."""
        price, ok = QInputDialog.getInt(self, "ورودی قیمت", "لطفاً هزینه بیعانه را وارد کنید:")

        if not ok:
            return

        try:
            total_text = self.ui.total_invoice_amount_label.text().replace("تومان", "").strip()
            total_text = persian_to_english_number(total_text)
            total_text = re.sub(r"[^\d]", "", total_text)
            total_amount = int(total_text)

            if price > total_amount:
                QMessageBox.warning(self, "مبلغ غیرمجاز",
                                    "مبلغ بیعانه نمی‌تواند بیش از مبلغ فاکتور باشد!")
                return

            self.advance_payment = price
            formatted_price = f"{price:,}"
            self.ui.advance_payment_label.setText(f"{to_persian_number(formatted_price)} تومان")

        except ValueError as e:
            QMessageBox.warning(self, "خطا", f"خطا در پردازش بیعانه: {e}")
        finally:
            self.update_payable_amount()

    def apply_discount(self):
        """Apply discount to invoice."""
        discount, ok = QInputDialog.getInt(self, "اعمال تخفیف", "درصد تخفیف:", 1, 1, 100)

        if not ok:
            return

        try:
            total_text = self.ui.total_invoice_amount_label.text().replace("تومان", "").strip()
            total_text = persian_to_english_number(total_text)
            total_text = re.sub(r"[^\d]", "", total_text)
            current_total = int(total_text)

            self.discount_amount = int((discount / 100) * current_total)
            formatted_discount = f"{self.discount_amount:,}"
            self.ui.discount_amount_label.setText(f"{to_persian_number(formatted_discount)} تومان")

        except ValueError as e:
            QMessageBox.warning(self, "خطا", f"خطا در اعمال تخفیف: {e}")
        finally:
            self.update_payable_amount()

    # Dialog Methods
    def open_calendar_dialog(self):
        """Open calendar dialog for delivery date."""
        from modules.PersianCalendar import CalendarDialog

        dialog = CalendarDialog()
        if dialog.exec():
            selected_date_time = dialog.get_selected_date_time()
            self.ui.delivery_date_label.setText(to_persian_number(selected_date_time))

    def open_language_dialog(self):
        """Open language selection dialog."""
        from modules.language_dialog import LanguageDialog

        current = self.ui.translation_languges_label.text()
        dialog = LanguageDialog(current, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected, set_default = dialog.get_selected_language()
            self.ui.translation_languges_label.setText(selected)

            if set_default:
                settings = QSettings("YourCompany", "YourApp")
                settings.setValue("default_language", selected)

    def open_send_dialog(self):
        """Open send invoice dialog."""
        from modules.InvoicePage.send_invoice import SendInvoice

        self.send_invoice = SendInvoice(self)
        self.send_invoice.exec()

    def open_remarks_dialog(self):
        """Open remarks editing dialog."""
        from modules.InvoicePage.invoice_remarks import RemarksDialog

        dialog = RemarksDialog(self)
        dialog.set_text(self.ui.textEdit.toHtml())

        if dialog.exec():
            self.ui.textEdit.setHtml(dialog.get_text())
            self.save_remarks()

    # Remarks Methods
    def save_remarks(self):
        """Save remarks to settings."""
        settings = QSettings("MyCompany", "InvoiceApp")
        settings.setValue("invoice_remarks", self.ui.textEdit.toHtml())

    def _load_remarks(self):
        """Load saved remarks from settings."""
        settings = QSettings("MyCompany", "InvoiceApp")
        saved_text = settings.value("invoice_remarks", "", type=str)
        self.ui.textEdit.setHtml(saved_text)

    # Resize Methods
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        self.adjust_table_columns(self.ui.tableWidget1, self.column_width)

    def adjust_table_columns(self, table_widget: QTableWidget, width_list: list):
        """Adjust table column widths."""
        header = table_widget.horizontalHeader()
        for i, length in enumerate(width_list):
            header.setSectionResizeMode(i, QHeaderView.Interactive)
            header.resizeSection(i, int(length))
        header.setStretchLastSection(True)

    # Save and Print Methods
    def save_invoice(self):
        """Save invoice as PNG or PDF."""
        clear_table_selection(self.ui.tableWidget1)
        total_pages = self.calculate_total_pages()

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "ذخیره فاکتور", "", "PNG Files (*.png);;PDF Files (*.pdf)"
        )

        if not file_path:
            return

        # Determine file extension
        base, ext = os.path.splitext(file_path)
        ext = ext.lower()
        if ext not in [".png", ".pdf"]:
            ext = ".png" if "PNG" in selected_filter else ".pdf"
            file_path = base + ext

        if ext == ".png":
            if total_pages > 1:
                QMessageBox.warning(self, "خطا",
                                    "فاکتورهایی که بیشتر از یک صفحه دارند را نمی‌توان با فرمت PNG ذخیره کرد. لطفا از فرمت PDF استفاده کنید.")
                return
            self.save_invoice_as_png(file_path)
        elif ext == ".pdf":
            self.save_invoice_as_pdf(file_path, total_pages)

        # Save to database
        if self.save_invoice_data(file_path):
            return file_path
        return None

    def save_invoice_as_png(self, file_path: str) -> bool:
        """Save invoice as PNG image."""
        clear_table_selection(self.ui.tableWidget1)
        with self.temporary_hide_footer():
            pixmap = self.grab()
            if pixmap.save(file_path, "PNG"):
                QMessageBox.information(self, "موفقیت",
                                        f"فاکتور موردنظر در آدرس زیر ذخیره شد:\n {file_path}")
                return True
            else:
                QMessageBox.critical(self, "خطا", "خطا در ذخیره‌سازی فاکتور")
                return False

    def save_invoice_as_pdf(self, file_path: str, total_pages: int) -> bool:
        """Save invoice as multi-page PDF."""
        clear_table_selection(self.ui.tableWidget1)

        # Setup printer
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(file_path)
        printer.setPageSize(QPageSize(QPageSize.A4))
        printer.setResolution(300)
        printer.setFullPage(True)

        painter = QPainter()

        # Hide navigation buttons
        self.ui.previous_page_button.setVisible(False)
        self.ui.next_page_button.setVisible(False)

        with self.temporary_hide_footer():
            try:
                original_page = self.current_page

                if not painter.begin(printer):
                    QMessageBox.critical(self, "خطا", "خطا در شروع فرایند چاپ PDF!")
                    return False

                for page in range(1, total_pages + 1):
                    self.current_page = page
                    self.update_pages()

                    self.ui.tableWidget1.viewport().update()
                    self.repaint()
                    QApplication.processEvents()

                    # Reset transformations and apply scaling
                    painter.resetTransform()
                    page_rect = printer.pageRect(QPrinter.DevicePixel)
                    pdf_width, pdf_height = page_rect.width(), page_rect.height()
                    widget_rect = self.rect()
                    widget_width, widget_height = widget_rect.width(), widget_rect.height()

                    scale_x = pdf_width / widget_width
                    scale_y = pdf_height / widget_height
                    painter.scale(scale_x, scale_y)

                    self.render(painter, QPoint(), QRegion(), QWidget.RenderFlag.DrawChildren)

                    if page < total_pages:
                        printer.newPage()

                painter.end()
                self.current_page = original_page
                self.update_pages()

                QMessageBox.information(self, "ذخیره فاکتور",
                                        f"فاکتور در آدرس زیر ذخیره شد:\n {file_path}")
                return True

            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در ذخیره‌سازی PDF: {str(e)}")
                return False
            finally:
                # Show navigation buttons again
                self.ui.previous_page_button.setVisible(True)
                self.ui.next_page_button.setVisible(True)

    @contextmanager
    def temporary_hide_footer(self):
        """Context manager to temporarily hide footer elements during save/print."""
        # Store original visibility states
        original_states = {
            'pages_gb': self.ui.pages_gb.isVisible(),
            'previous_button': self.ui.previous_page_button.isVisible(),
            'next_button': self.ui.next_page_button.isVisible()
        }

        try:
            # Hide elements
            self.ui.pages_gb.setVisible(False)
            self.ui.previous_page_button.setVisible(False)
            self.ui.next_page_button.setVisible(False)
            yield
        finally:
            # Restore original states
            self.ui.pages_gb.setVisible(original_states['pages_gb'])
            self.ui.previous_page_button.setVisible(original_states['previous_button'])
            self.ui.next_page_button.setVisible(original_states['next_button'])

    def print_form(self):
        """Print the invoice form."""
        clear_table_selection(self.ui.tableWidget1)

        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.A4))
        printer.setResolution(300)

        print_dialog = QPrintDialog(printer, self)

        if print_dialog.exec() != QPrintDialog.DialogCode.Accepted:
            return

        total_pages = self.calculate_total_pages()
        painter = QPainter()

        # Hide navigation buttons during printing
        self.ui.previous_page_button.setVisible(False)
        self.ui.next_page_button.setVisible(False)

        with self.temporary_hide_footer():
            try:
                original_page = self.current_page

                if not painter.begin(printer):
                    QMessageBox.critical(self, "خطا", "خطا در شروع فرایند چاپ!")
                    return

                for page in range(1, total_pages + 1):
                    self.current_page = page
                    self.update_pages()

                    # Ensure UI updates
                    self.ui.tableWidget1.viewport().update()
                    self.repaint()
                    QApplication.processEvents()

                    # Calculate scaling
                    page_rect = printer.pageRect(QPrinter.DevicePixel)
                    pdf_width, pdf_height = page_rect.width(), page_rect.height()
                    widget_rect = self.rect()
                    widget_width, widget_height = widget_rect.width(), widget_rect.height()

                    scale_x = pdf_width / widget_width
                    scale_y = pdf_height / widget_height
                    scale = min(scale_x, scale_y) * self.scale_factor

                    painter.resetTransform()
                    painter.scale(scale, scale)

                    # Center the content
                    x_offset = (pdf_width / scale - widget_width) / 2
                    y_offset = (pdf_height / scale - widget_height) / 2
                    painter.translate(x_offset, y_offset)

                    self.render(painter, QPoint(), QRegion(), QWidget.RenderFlag.DrawChildren)

                    if page < total_pages:
                        printer.newPage()

                painter.end()
                self.current_page = original_page
                self.update_pages()

                QMessageBox.information(self, "چاپ", "فاکتور با موفقیت چاپ شد.")

            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در چاپ: {str(e)}")
            finally:
                # Show navigation buttons again
                self.ui.previous_page_button.setVisible(True)
                self.ui.next_page_button.setVisible(True)

    def calculate_invoice_summary(self) -> InvoiceSummary:
        """
        Calculate invoice summary from table data.
        You'll need to implement this method based on your table structure.
        This is a placeholder implementation.
        """
        # Initialize counters
        total_official_docs = 0
        total_unofficial_docs = 0
        total_pages = 0
        total_judiciary = 0
        total_foreign_affairs = 0
        total_additional_docs = 0
        total_translation_price = 0

        # Process self.all_table_data to calculate these values
        # This depends on your table structure - you'll need to adapt this
        for row_data in getattr(self, 'all_table_data', []):
            # Add your logic here to extract and sum up the values
            # Example (adapt to your table structure):
            # if len(row_data) > 5:  # Assuming indices for different columns
            #     total_official_docs += int(row_data[2] or 0)
            #     total_unofficial_docs += int(row_data[3] or 0)
            #     total_pages += int(row_data[4] or 0)
            #     # ... etc
            pass

        return InvoiceSummary(
            total_official_docs_count=total_official_docs,
            total_unofficial_docs_count=total_unofficial_docs,
            total_pages_count=total_pages,
            total_judiciary_count=total_judiciary,
            total_foreign_affairs_count=total_foreign_affairs,
            total_additional_doc_count=total_additional_docs,
            total_translation_price=total_translation_price
        )

    def save_invoice_data(self, file_path: str) -> bool:
        """Save invoice data to the database."""
        try:
            # Get current username
            current_username = self.get_current_username()
            if not current_username:
                QMessageBox.warning(self, "خطا", "نمی‌توان کاربر فعلی را شناسایی کرد.")
                return False

            # Calculate or get invoice summary data
            # You'll need to replace these with actual method calls or calculations
            invoice_summary = self.calculate_invoice_summary()  # Implement this method

            # Prepare invoice data
            invoice_data = {
                'invoice_number': self.invoice_no,
                'name': self.customer_name,
                'national_id': self.national_id,
                'phone': self.phone_no,
                'issue_date': self.issue_date,
                'delivery_date': self.ui.delivery_date_label.text(),
                'translator': self.get_user_full_name_from_username(current_username),
                'total_amount': float(self.invoice_price),
                'advance_payment': getattr(self, 'advance_payment', 0),
                'discount_amount': getattr(self, 'discount_amount', 0),
                'final_amount': self.calculate_final_amount(),
                'language': self.ui.translation_languges_label.text(),
                'remarks': self.ui.textEdit.toPlainText(),
                'pdf_file_path': file_path,
                'username': current_username,
                'table_data': json.dumps(self.all_table_data, ensure_ascii=False),
                'invoice_status': 0,  # Default status (0 = draft, 1 = finalized)
                # Add InvoiceSummary fields
                'total_official_docs_count': invoice_summary.total_official_docs_count,
                'total_unofficial_docs_count': invoice_summary.total_unofficial_docs_count,
                'total_pages_count': invoice_summary.total_pages_count,
                'total_judiciary_count': invoice_summary.total_judiciary_count,
                'total_foreign_affairs_count': invoice_summary.total_foreign_affairs_count,
                'total_additional_doc_count': invoice_summary.total_additional_doc_count,
                'total_translation_price': invoice_summary.total_translation_price
            }

            # Save to database
            with sqlite3.connect(INVOICES_DATABASE) as connection:
                cursor = connection.cursor()

                # Insert or update invoice in issued_invoices table
                cursor.execute("""
                    INSERT OR REPLACE INTO issued_invoices 
                    (invoice_number, name, national_id, phone, issue_date, 
                     delivery_date, translator, total_amount, advance_payment, discount_amount, 
                     final_amount, language, remarks, pdf_file_path, username, table_data, invoice_status,
                     total_official_docs_count, total_unofficial_docs_count, total_pages_count,
                     total_judiciary_count, total_foreign_affairs_count, total_additional_doc_count,
                     total_translation_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    invoice_data['invoice_number'], invoice_data['name'],
                    invoice_data['national_id'], invoice_data['phone'],
                    invoice_data['issue_date'], invoice_data['delivery_date'],
                    invoice_data['translator'], invoice_data['total_amount'],
                    invoice_data['advance_payment'], invoice_data['discount_amount'],
                    invoice_data['final_amount'], invoice_data['language'],
                    invoice_data['remarks'], invoice_data['pdf_file_path'],
                    invoice_data['username'], invoice_data['table_data'],
                    invoice_data['invoice_status'],
                    invoice_data['total_official_docs_count'],
                    invoice_data['total_unofficial_docs_count'],
                    invoice_data['total_pages_count'],
                    invoice_data['total_judiciary_count'],
                    invoice_data['total_foreign_affairs_count'],
                    invoice_data['total_additional_doc_count'],
                    invoice_data['total_translation_price']
                ))

                # Save individual items to invoice_items table
                # First, delete existing items for this invoice
                cursor.execute("DELETE FROM invoice_items WHERE invoice_number = ?", (invoice_data['invoice_number'],))

                # Insert new items
                for row_data in self.all_table_data:
                    if len(row_data) > 1 and row_data[1].strip():  # Assuming column 1 contains item description
                        cursor.execute("""
                            INSERT INTO invoice_items (invoice_number, items)
                            VALUES (?, ?)
                        """, (invoice_data['invoice_number'], row_data[1]))

                connection.commit()
                return True

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در ذخیره داده‌ها: {str(e)}")
            return False
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطای غیرمنتظره: {str(e)}")
            return False

    def calculate_final_amount(self) -> int:
        """Calculate the final payable amount."""
        try:
            total_text = self.ui.total_invoice_amount_label.text().replace("تومان", "").strip()
            total_text = persian_to_english_number(total_text)
            total_text = re.sub(r"[^\d]", "", total_text)
            total_amount = int(total_text)

            advance_payment = int(getattr(self, "advance_payment", 0) or 0)
            discount_amount = int(getattr(self, "discount_amount", 0) or 0)

            return max(0, total_amount - advance_payment - discount_amount)
        except (ValueError, AttributeError):
            return 0

    def load_invoice_from_database(self, invoice_number: int) -> bool:
        """Load an existing invoice from the database."""
        try:
            with sqlite3.connect(INVOICES_DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute("""
                    SELECT * FROM issued_invoices WHERE invoice_number = ?
                """, (invoice_number,))

                result = cursor.fetchone()
                if not result:
                    return False

                # Map result to invoice data
                columns = [description[0] for description in cursor.description]
                invoice_data = dict(zip(columns, result))

                # Restore invoice data with correct column names
                self.invoice_no = str(invoice_data['invoice_number'])
                self.customer_name = invoice_data['name']
                self.national_id = str(invoice_data['national_id'])
                self.phone_no = invoice_data['phone']
                self.issue_date = invoice_data['issue_date']
                self.invoice_price = int(invoice_data['total_amount'])
                self.advance_payment = invoice_data.get('advance_payment', 0)
                self.discount_amount = invoice_data.get('discount_amount', 0)

                # Restore InvoiceSummary data
                self.invoice_summary = InvoiceSummary(
                    total_official_docs_count=invoice_data.get('total_official_docs_count', 0),
                    total_unofficial_docs_count=invoice_data.get('total_unofficial_docs_count', 0),
                    total_pages_count=invoice_data.get('total_pages_count', 0),
                    total_judiciary_count=invoice_data.get('total_judiciary_count', 0),
                    total_foreign_affairs_count=invoice_data.get('total_foreign_affairs_count', 0),
                    total_additional_doc_count=invoice_data.get('total_additional_doc_count', 0),
                    total_translation_price=invoice_data.get('total_translation_price', 0)
                )

                # Restore table data
                if invoice_data.get('table_data'):
                    self.all_table_data = json.loads(invoice_data['table_data'])

                # Update UI
                self._set_labels()
                self.ui.delivery_date_label.setText(invoice_data.get('delivery_date', ''))
                self.ui.translation_languges_label.setText(invoice_data.get('language', 'انگلیسی'))
                self.ui.textEdit.setPlainText(invoice_data.get('remarks', ''))

                # Update payment labels
                if self.advance_payment:
                    formatted_price = f"{self.advance_payment:,}"
                    self.ui.advance_payment_label.setText(f"{to_persian_number(formatted_price)} تومان")

                if self.discount_amount:
                    formatted_discount = f"{self.discount_amount:,}"
                    self.ui.discount_amount_label.setText(f"{to_persian_number(formatted_discount)} تومان")

                self.update_payable_amount()
                self.update_pages()

                return True

        except (sqlite3.Error, json.JSONDecodeError) as e:
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری فاکتور: {str(e)}")
            return False

    def delete_invoice_from_database(self, invoice_number: int) -> bool:
        """Delete an invoice from the database."""
        try:
            reply = QMessageBox.question(self, "تأیید حذف",
                                         f"آیا مطمئن هستید که می‌خواهید فاکتور شماره {invoice_number} را حذف کنید؟",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)

            if reply != QMessageBox.StandardButton.Yes:
                return False

            with sqlite3.connect(INVOICES_DATABASE) as connection:
                cursor = connection.cursor()
                # Delete from issued_invoices (items will be deleted automatically due to CASCADE)
                cursor.execute("DELETE FROM issued_invoices WHERE invoice_number = ?", (invoice_number,))

                if cursor.rowcount > 0:
                    connection.commit()
                    QMessageBox.information(self, "موفقیت", "فاکتور با موفقیت حذف شد.")
                    return True
                else:
                    QMessageBox.warning(self, "خطا", "فاکتور مورد نظر یافت نشد.")
                    return False

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطا", f"خطا در حذف فاکتور: {str(e)}")
            return False

    def get_all_invoices_for_user(self, username: str = None) -> list:
        """Get all invoices for a specific user or current user."""
        try:
            if not username:
                username = self.get_current_username()

            if not username:
                return []

            with sqlite3.connect(INVOICES_DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute("""
                    SELECT invoice_number, name, issue_date, total_amount, final_amount, invoice_status,
                           total_official_docs_count, total_unofficial_docs_count, total_pages_count,
                           total_judiciary_count, total_foreign_affairs_count, total_additional_doc_count,
                           total_translation_price
                    FROM issued_invoices 
                    WHERE username = ? 
                    ORDER BY issue_date DESC
                """, (username,))

                return cursor.fetchall()

        except sqlite3.Error as e:
            print(f"Error fetching invoices: {e}")
            return []

    def export_invoices_to_excel(self, file_path: str, username: str = None) -> bool:
        """Export invoices to Excel file."""
        try:
            import pandas as pd

            if not username:
                username = self.get_current_username()

            if not username:
                QMessageBox.warning(self, "خطا", "نمی‌توان کاربر فعلی را شناسایی کرد.")
                return False

            with sqlite3.connect(INVOICES_DATABASE) as connection:
                query = """
                    SELECT invoice_number as 'شماره فاکتور', 
                           name as 'نام مشتری',
                           national_id as 'کد ملی',
                           phone as 'شماره تلفن',
                           issue_date as 'تاریخ صدور',
                           delivery_date as 'تاریخ تحویل',
                           translator as 'مترجم',
                           total_official_docs_count as 'تعداد اسناد رسمی',
                           total_unofficial_docs_count as 'تعداد اسناد غیررسمی',
                           total_pages_count as 'تعداد صفحات',
                           total_judiciary_count as 'تعداد قضایی',
                           total_foreign_affairs_count as 'تعداد امور خارجه',
                           total_additional_doc_count as 'تعداد اسناد اضافی',
                           total_translation_price as 'قیمت ترجمه',
                           total_amount as 'مبلغ فاکتور',
                           advance_payment as 'بیعانه',
                           discount_amount as 'تخفیف',
                           final_amount as 'مبلغ نهایی',
                           language as 'زبان ترجمه',
                           invoice_status as 'وضعیت فاکتور'
                    FROM issued_invoices 
                    WHERE username = ? 
                    ORDER BY issue_date DESC
                """

                df = pd.read_sql_query(query, connection, params=(username,))

                if df.empty:
                    QMessageBox.information(self, "اطلاع", "هیچ فاکتوری برای خروجی یافت نشد.")
                    return False

                # Convert invoice_status to readable format
                df['وضعیت فاکتور'] = df['وضعیت فاکتور'].map({0: 'پیش‌نویس', 1: 'نهایی'})

                # Save to Excel
                df.to_excel(file_path, index=False, engine='openpyxl')
                QMessageBox.information(self, "موفقیت",
                                        f"اطلاعات فاکتورها در فایل زیر ذخیره شد:\n{file_path}")
                return True

        except ImportError:
            QMessageBox.critical(self, "خطا",
                                 "برای خروجی Excel، نیاز به نصب کتابخانه pandas و openpyxl دارید.")
            return False
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در خروجی Excel: {str(e)}")
            return False

    def backup_invoices_database(self, backup_path: str) -> bool:
        """Create a backup of the invoices database."""
        try:
            import shutil
            shutil.copy2(INVOICES_DATABASE, backup_path)
            QMessageBox.information(self, "موفقیت",
                                    f"پشتیبان‌گیری از پایگاه داده در آدرس زیر انجام شد:\n{backup_path}")
            return True
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در پشتیبان‌گیری: {str(e)}")
            return False

    def get_invoice_items(self, invoice_number: int) -> list:
        """Get all items for a specific invoice."""
        try:
            with sqlite3.connect(INVOICES_DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute("""
                    SELECT items FROM invoice_items 
                    WHERE invoice_number = ?
                    ORDER BY id
                """, (invoice_number,))

                return [row[0] for row in cursor.fetchall()]

        except sqlite3.Error as e:
            print(f"Error fetching invoice items: {e}")
            return []

    def update_invoice_status(self, invoice_number: int, status: int) -> bool:
        """Update the status of an invoice (0 = draft, 1 = finalized)."""
        try:
            with sqlite3.connect(INVOICES_DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute("""
                    UPDATE issued_invoices 
                    SET invoice_status = ? 
                    WHERE invoice_number = ?
                """, (status, invoice_number))

                if cursor.rowcount > 0:
                    connection.commit()
                    status_text = "نهایی" if status == 1 else "پیش‌نویس"
                    QMessageBox.information(self, "موفقیت", f"وضعیت فاکتور به '{status_text}' تغییر یافت.")
                    return True
                else:
                    QMessageBox.warning(self, "خطا", "فاکتور مورد نظر یافت نشد.")
                    return False

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطا", f"خطا در به‌روزرسانی وضعیت: {str(e)}")
            return False

    def get_invoice_statistics(self, username: str = None) -> dict:
        """Get statistics about invoices for a user."""
        try:
            if not username:
                username = self.get_current_username()

            if not username:
                return {}

            with sqlite3.connect(INVOICES_DATABASE) as connection:
                cursor = connection.cursor()

                # Get basic statistics including InvoiceSummary fields
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_invoices,
                        COUNT(CASE WHEN invoice_status = 0 THEN 1 END) as draft_invoices,
                        COUNT(CASE WHEN invoice_status = 1 THEN 1 END) as final_invoices,
                        SUM(total_amount) as total_revenue,
                        AVG(total_amount) as average_invoice_amount,
                        SUM(advance_payment) as total_advances,
                        SUM(discount_amount) as total_discounts,
                        SUM(total_official_docs_count) as total_official_docs,
                        SUM(total_unofficial_docs_count) as total_unofficial_docs,
                        SUM(total_pages_count) as total_pages,
                        SUM(total_judiciary_count) as total_judiciary,
                        SUM(total_foreign_affairs_count) as total_foreign_affairs,
                        SUM(total_additional_doc_count) as total_additional_docs,
                        SUM(total_translation_price) as total_translation_revenue
                    FROM issued_invoices 
                    WHERE username = ?
                """, (username,))

                result = cursor.fetchone()
                if result:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, result))

                return {}

        except sqlite3.Error as e:
            print(f"Error getting invoice statistics: {e}")
            return {}

    def closeEvent(self, event):
        """Handle dialog close event."""
        # Save current settings
        self.save_remarks()

        # Save window geometry
        if hasattr(self, 'settings'):
            self.settings.setValue("geometry", self.saveGeometry())

        event.accept()

    def keyPressEvent(self, event):
        """Handle key press events for navigation shortcuts."""
        if event.key() == Qt.Key.Key_Right or event.key() == Qt.Key.Key_PageDown:
            self.next_page()
        elif event.key() == Qt.Key.Key_Left or event.key() == Qt.Key.Key_PageUp:
            self.previous_page()
        elif event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_S:
                self.save_invoice()
            elif event.key() == Qt.Key.Key_P:
                self.print_form()
        else:
            super().keyPressEvent(event)

# Utility functions for the invoice system


# Example usage and testing functions

# if __name__ == "__main__":
#     import sys
#     from PySide6.QtWidgets import QApplication
#
#     app = QApplication(sys.argv)
#
#     # This would normally be called with actual parent widget and settings
#     # For testing purposes, you can create a minimal setup
#
#     class MockParentWidget:
#         """Mock parent widget for testing purposes."""
#
#         def __init__(self):
#             self.ui = self
#             self.full_name_le = type('obj', (object,), {'text': lambda: 'نام تستی'})
#             self.national_id_le = type('obj', (object,), {'text': lambda: '1234567890'})
#             self.phone_le = type('obj', (object,), {'text': lambda: '09123456789'})
#             self.tableWidget = QTableWidget(5, 7)
#
#             # Add some test data
#             for row in range(5):
#                 for col in range(7):
#                     item = QTableWidgetItem(f"Test {row}-{col}")
#                     self.tableWidget.setItem(row, col, item)
#
#         def get_current_invoice_no(self):
#             return "12345"
#
#     class MockSettings:
#         """Mock settings for testing purposes."""
#
#         def __init__(self):
#             self.scale = "100%"
#
#     # Uncomment the following lines for testing
#     mock_parent = MockParentWidget()
#     mock_settings = MockSettings()
#     dialog = create_invoice_preview(mock_parent, mock_settings)
#     if dialog:
#         dialog.show()
#         sys.exit(app.exec())
