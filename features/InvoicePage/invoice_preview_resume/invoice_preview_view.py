"""
View layer for invoice preview functionality using PySide6.
Handles UI updates and user interactions.
"""

import os
import sys
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from PySide6.QtCore import Qt, QSize, QSettings, QPoint
from PySide6.QtWidgets import (
    QDialog, QWidget, QMessageBox, QInputDialog, QFileDialog,
    QTableWidget, QTableWidgetItem, QTextEdit, QLabel, QPushButton,
    QHeaderView, QAbstractItemView, QApplication, QSizePolicy
)
from PySide6.QtGui import QFont, QTextCharFormat, QTextCursor, QPixmap, QPainter, QRegion, QPageSize
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from features.InvoicePage.invoice_preview_resume.invoice_preview_models import InvoiceData
from features.InvoicePage.invoice_preview_resume.invoice_preview_controller import InvoicePreviewController


class InvoicePreviewView(QDialog):
    """
    Main view class for invoice preview functionality.
    Handles UI display and user interactions.
    """

    def __init__(self, controller: InvoicePreviewController, parent_invoice_widget, username: str):
        super().__init__()

        self.controller = controller
        self.parent_invoice_widget = parent_invoice_widget
        self.username = username
        self.original_geometry = None
        self.original_sizes = {}

        # Initialize UI
        self._setup_ui()
        self._connect_signals()
        self._configure_window()

        # Initialize controller
        self.controller.initialize_invoice(parent_invoice_widget, username)

    def _setup_ui(self):
        """Setup the user interface."""
        # Load the appropriate UI based on scale settings
        scale_config = self.controller.scale_config

        try:
            ui_module = __import__(scale_config.ui_module, fromlist=['Ui_MainLayout'])
            Ui_MainLayout = ui_module.Ui_MainLayout
            self.ui = Ui_MainLayout()
            self.ui.setupUi(self)
        except ImportError as e:
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری رابط کاربری: {str(e)}")
            return

        # Store original geometry and sizes
        self.original_geometry = self.geometry()
        for widget in self.findChildren(QWidget):
            self.original_sizes[widget] = widget.size()

        # Apply styles
        self._apply_styles()

        # Configure table
        self._configure_table()

        # Hide pages initially
        if hasattr(self.ui, 'pages_gb'):
            self.ui.pages_gb.hide()

    def _apply_styles(self):
        """Apply custom stylesheet."""
        try:
            # You should define STYLES_ABSOLUTE_PATH or load styles from resources
            styles_path = "styles/invoice_preview.qss"  # Adjust path as needed
            if os.path.exists(styles_path):
                with open(styles_path, "r") as style_file:
                    stylesheet = style_file.read()
                    self.setStyleSheet(stylesheet)
        except FileNotFoundError:
            print(f"Warning: Style file not found")

    def _configure_window(self):
        """Configure window properties."""
        self.setWindowTitle("پیش‌نمایش فاکتور")
        self.setFixedSize(self.size())

        # Set window modality
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

    def _configure_table(self):
        """Configure table widget properties."""
        if not hasattr(self.ui, 'tableWidget1'):
            return

        table = self.ui.tableWidget1

        # Size policy
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Header configuration
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Disable editing
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Configure column widths
        self._adjust_table_columns()

    def _adjust_table_columns(self):
        """Adjust table column widths based on scale configuration."""
        if not hasattr(self.ui, 'tableWidget1'):
            return

        table = self.ui.tableWidget1
        header = table.horizontalHeader()
        column_widths = self.controller.scale_config.column_width

        for i, width in enumerate(column_widths):
            if i < table.columnCount():
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
                header.resizeSection(i, int(width))

        # Set last section to stretch
        header.setStretchLastSection(True)

    def _connect_signals(self):
        """Connect controller signals to view methods."""
        self.controller.invoice_loaded.connect(self._on_invoice_loaded)
        self.controller.page_changed.connect(self._on_page_changed)
        self.controller.amounts_updated.connect(self._on_amounts_updated)
        self.controller.error_occurred.connect(self._show_error_message)
        self.controller.success_message.connect(self._show_success_message)
        self.controller.export_completed.connect(self._on_export_completed)

        # Connect UI buttons
        self._connect_ui_buttons()

    def _connect_ui_buttons(self):
        """Connect UI button signals."""
        button_connections = {
            'print_invoice_button': self._on_print_clicked,
            'save_invoice_button': self._on_save_clicked,
            'send_email_button': self._on_send_email_clicked,
            'delivery_date_button': self._on_delivery_date_clicked,
            'translation_languages_button': self._on_language_clicked,
            'next_page_button': self._on_next_page_clicked,
            'previous_page_button': self._on_previous_page_clicked,
            'discount_button': self._on_discount_clicked,
            'advance_payment_button': self._on_advance_payment_clicked,
            'attention_button': self._on_remarks_clicked
        }

        for button_name, slot in button_connections.items():
            if hasattr(self.ui, button_name):
                button = getattr(self.ui, button_name)
                if isinstance(button, QPushButton):
                    button.clicked.connect(slot)
                else:
                    # For other clickable widgets, you might need to handle differently
                    # Since we're removing ClickableLabel, we'll need regular buttons or labels
                    pass

    def _on_invoice_loaded(self, invoice_data: InvoiceData):
        """Handle invoice loaded signal."""
        self._update_invoice_labels(invoice_data)
        self._update_amounts_display()
        self._populate_table()
        self._update_page_visibility()

    def _on_page_changed(self, page_number: int):
        """Handle page changed signal."""
        self._populate_table()
        self._update_page_visibility()
        self._update_page_label()

    def _on_amounts_updated(self, amounts: Dict[str, int]):
        """Handle amounts updated signal."""
        formatted_amounts = self.controller.get_formatted_amounts()

        # Update amount labels
        if hasattr(self.ui, 'total_invoice_amount_label'):
            self.ui.total_invoice_amount_label.setText(formatted_amounts['total_amount'])
        if hasattr(self.ui, 'advance_payment_label'):
            self.ui.advance_payment_label.setText(formatted_amounts['advance_payment'])
        if hasattr(self.ui, 'discount_amount_label'):
            self.ui.discount_amount_label.setText(formatted_amounts['discount_amount'])
        if hasattr(self.ui, 'total_payable_amount_label'):
            self.ui.total_payable_amount_label.setText(formatted_amounts['final_amount'])

    def _update_invoice_labels(self, invoice_data: InvoiceData):
        """Update UI labels with invoice data."""
        # Get translation office info
        office_info = self.controller.get_translation_office_info()

        # Customer information
        if hasattr(self.ui, 'customer_name_label'):
            self.ui.customer_name_label.setText(invoice_data.customer_name)
        if hasattr(self.ui, 'customer_phone_label'):
            self.ui.customer_phone_label.setText(self._to_persian_number(invoice_data.phone))
        if hasattr(self.ui, 'national_id_label'):
            self.ui.national_id_label.setText(self._to_persian_number(invoice_data.national_id))

        # Invoice information
        if hasattr(self.ui, 'receipt_no_label'):
            self.ui.receipt_no_label.setText(self._to_persian_number(str(invoice_data.invoice_number)))
        if hasattr(self.ui, 'receive_date_lable'):
            self.ui.receive_date_lable.setText(self._to_persian_number(str(invoice_data.issue_date)))
        if hasattr(self.ui, 'user_name_text'):
            self.ui.user_name_text.setText(invoice_data.translator)

        # Translation office information
        if hasattr(self.ui, 'translation_office_label'):
            self.ui.translation_office_label.setText(office_info['name'])
        if hasattr(self.ui, 'registration_no_label'):
            self.ui.registration_no_label.setText(f"شماره ثبت: {office_info['reg_no']}")
        if hasattr(self.ui, 'tro_address_text'):
            self.ui.tro_address_text.setText(f"آدرس: {office_info['address']}")
        if hasattr(self.ui, 'tro_phone_text'):
            self.ui.tro_phone_text.setText(f"شماره تماس: {office_info['phone']}")
        if hasattr(self.ui, 'tro_email_text'):
            self.ui.tro_email_text.setText(f"ایمیل: {office_info['website']}")

        # Language
        if hasattr(self.ui, 'translation_languges_label'):
            lang_text = invoice_data.target_language or "انگلیسی"
            self.ui.translation_languges_label.setText(lang_text)

        # Delivery date
        if hasattr(self.ui, 'delivery_date_label') and invoice_data.delivery_date:
            self.ui.delivery_date_label.setText(self._to_persian_number(str(invoice_data.delivery_date)))

    def _update_amounts_display(self):
        """Update amount displays."""
        formatted_amounts = self.controller.get_formatted_amounts()

        if hasattr(self.ui, 'total_invoice_amount_label'):
            self.ui.total_invoice_amount_label.setText(formatted_amounts['total_amount'])
        if hasattr(self.ui, 'advance_payment_label'):
            self.ui.advance_payment_label.setText(formatted_amounts['advance_payment'])
        if hasattr(self.ui, 'discount_amount_label'):
            self.ui.discount_amount_label.setText(formatted_amounts['discount_amount'])
        if hasattr(self.ui, 'total_payable_amount_label'):
            self.ui.total_payable_amount_label.setText(formatted_amounts['final_amount'])

    def _populate_table(self):
        """Populate table with current page data."""
        if not hasattr(self.ui, 'tableWidget1'):
            return

        table = self.ui.tableWidget1
        page_data, start_idx, end_idx = self.controller.get_current_page_data()

        # Clear and set row count
        table.clearContents()
        table.setRowCount(len(page_data))

        # Populate table
        for row_idx, row_data in enumerate(page_data):
            # Add row number
            absolute_row_number = start_idx + row_idx + 1
            table.setItem(row_idx, 0, QTableWidgetItem(self._to_persian_number(str(absolute_row_number))))

            # Add data columns
            for col_idx, col_value in enumerate(row_data):
                if col_idx < table.columnCount() - 1:  # Skip last column for row numbers
                    item = QTableWidgetItem(self._to_persian_number(str(col_value)))
                    # Center align except for item name column
                    if col_idx == 1:  # Item name column
                        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    else:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    table.setItem(row_idx, col_idx + 1, item)

    def _update_page_visibility(self):
        """Update visibility of UI elements based on current page."""
        visibility_config = self.controller.get_page_visibility_config()

        # Show/hide elements based on page
        if hasattr(self.ui, 'header_frame'):
            self.ui.header_frame.setVisible(visibility_config['show_header'])
        if hasattr(self.ui, 'groupBox_6'):  # Customer info group
            self.ui.groupBox_6.setVisible(visibility_config['show_customer_info'])
        if hasattr(self.ui, 'price_sign_frame'):
            self.ui.price_sign_frame.setVisible(visibility_config['show_price_summary'])
        if hasattr(self.ui, 'pages_gb'):
            self.ui.pages_gb.setVisible(visibility_config['show_pagination'])

    def _update_page_label(self):
        """Update page number label."""
        if hasattr(self.ui, 'page_label'):
            current_page = self.controller.current_page
            total_pages = self.controller.pagination_config.total_pages
            page_text = f"صفحه {self._to_persian_number(str(current_page))} از {self._to_persian_number(str(total_pages))}"
            self.ui.page_label.setText(page_text)

    # Button event handlers
    def _on_next_page_clicked(self):
        """Handle next page button click."""
        self.controller.next_page()

    def _on_previous_page_clicked(self):
        """Handle previous page button click."""
        self.controller.previous_page()

    def _on_discount_clicked(self):
        """Handle discount button click."""
        discount_percentage, ok = QInputDialog.getInt(
            self, "اعمال تخفیف", "درصد تخفیف:", 1, 1, 100
        )

        if ok:
            self.controller.apply_discount(discount_percentage)

    def _on_advance_payment_clicked(self):
        """Handle advance payment button click."""
        amount, ok = QInputDialog.getInt(
            self, "ورودی قیمت", "لطفاً هزینه بیعانه را وارد کنید:"
        )

        if ok:
            self.controller.set_advance_payment(amount)

    def _on_delivery_date_clicked(self):
        """Handle delivery date button click."""
        try:
            from modules.PersianCalendar import CalendarDialog
            dialog = CalendarDialog()
            if dialog.exec():
                selected_date = dialog.get_selected_date()
                self.controller.update_delivery_date(selected_date)
                if hasattr(self.ui, 'delivery_date_label'):
                    self.ui.delivery_date_label.setText(self._to_persian_number(str(selected_date)))
        except ImportError:
            QMessageBox.warning(self, "خطا", "ماژول تقویم یافت نشد")

    def _on_language_clicked(self):
        """Handle language button click."""
        try:
            from modules.language_dialog import LanguageDialog
            current = self.ui.translation_languges_label.text() if hasattr(self.ui, 'translation_languges_label') else "انگلیسی"
            dialog = LanguageDialog(current, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected, set_default = dialog.get_selected_language()
                self.controller.update_language("", selected)  # You might want to handle source language too
                if hasattr(self.ui, 'translation_languges_label'):
                    self.ui.translation_languges_label.setText(selected)

                if set_default:
                    settings = QSettings("YourCompany", "YourApp")
                    settings.setValue("default_language", selected)
        except ImportError:
            QMessageBox.warning(self, "خطا", "ماژول انتخاب زبان یافت نشد")

    def _on_remarks_clicked(self):
        """Handle remarks button click."""
        try:
            from modules.InvoicePage.invoice_remarks import RemarksDialog
            dialog = RemarksDialog(self)

            # Set current text
            if hasattr(self.ui, 'textEdit'):
                dialog.set_text(self.ui.textEdit.toHtml())

            if dialog.exec():
                new_text = dialog.get_text()
                self.controller.update_remarks(new_text)
                if hasattr(self.ui, 'textEdit'):
                    self.ui.textEdit.setHtml(new_text)
        except ImportError:
            QMessageBox.warning(self, "خطا", "ماژول ویرایش توضیحات یافت نشد")

    def _on_send_email_clicked(self):
        """Handle send email button click."""
        try:
            from modules.InvoicePage.send_invoice import SendInvoice
            dialog = SendInvoice(self)
            dialog.exec()
        except ImportError:
            QMessageBox.warning(self, "خطا", "ماژول ارسال ایمیل یافت نشد")

    def _on_save_clicked(self):
        """Handle save button click."""
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "ذخیره فاکتور",
            self.controller.generate_suggested_filename("png"),
            "PNG Files (*.png);;PDF Files (*.pdf)"
        )

        if not file_path:
            return

        # Determine file type
        if file_path.lower().endswith('.png'):
            self._save_as_png(file_path)
        elif file_path.lower().endswith('.pdf'):
            self._save_as_pdf(file_path)
        else:
            # Auto-detect from filter
            if "PNG" in selected_filter:
                if not file_path.endswith('.png'):
                    file_path += '.png'
                self._save_as_png(file_path)
            else:
                if not file_path.endswith('.pdf'):
                    file_path += '.pdf'
                self._save_as_pdf(file_path)

    def _save_as_png(self, file_path: str):
        """Save invoice as PNG image."""
        self._clear_table_selection()

        with self._temporary_hide_footer():
            pixmap = self.grab()
            self.controller.save_invoice_as_png(file_path, pixmap)

    def _save_as_pdf(self, file_path: str):
        """Save invoice as multi-page PDF."""
        self._clear_table_selection()

        # Setup printer
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(file_path)
        printer.setPageSize(QPageSize.PageSizeId.A4)
        printer.setResolution(300)
        printer.setFullPage(True)

        painter = QPainter()

        with self._temporary_hide_footer():
            try:
                original_page = self.controller.current_page
                total_pages = self.controller.pagination_config.total_pages

                if not painter.begin(printer):
                    QMessageBox.critical(self, "خطا", "خطا در شروع فرایند چاپ PDF!")
                    return

                for page in range(1, total_pages + 1):
                    self.controller.navigate_to_page(page)

                    # Update display
                    QApplication.processEvents()

                    # Calculate scaling
                    page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
                    pdf_width, pdf_height = page_rect.width(), page_rect.height()
                    widget_rect = self.rect()
                    widget_width, widget_height = widget_rect.width(), widget_rect.height()

                    scale_x = pdf_width / widget_width
                    scale_y = pdf_height / widget_height
                    painter.resetTransform()
                    painter.scale(scale_x, scale_y)

                    self.render(painter, QPoint(), QRegion(), QWidget.RenderFlag.DrawChildren)

                    if page < total_pages:
                        printer.newPage()

                painter.end()
                self.controller.navigate_to_page(original_page)
                self.controller.save_invoice_as_pdf(file_path)

            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در ذخیره‌سازی PDF: {str(e)}")
                if painter.isActive():
                    painter.end()

    def _on_print_clicked(self):
        """Handle print button click."""
        self._clear_table_selection()

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize.PageSizeId.A4)
        printer.setResolution(300)

        print_dialog = QPrintDialog(printer, self)

        if print_dialog.exec() != QPrintDialog.DialogCode.Accepted:
            return

        self._print_to_printer(printer)

    def _print_to_printer(self, printer: QPrinter):
        """Print invoice to printer."""
        painter = QPainter()
        total_pages = self.controller.pagination_config.total_pages

        with self._temporary_hide_footer():
            try:
                original_page = self.controller.current_page

                if not painter.begin(printer):
                    QMessageBox.critical(self, "خطا", "خطا در شروع فرایند چاپ!")
                    return

                for page in range(1, total_pages + 1):
                    self.controller.navigate_to_page(page)
                    QApplication.processEvents()

                    # Calculate scaling
                    page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
                    pdf_width, pdf_height = page_rect.width(), page_rect.height()
                    widget_rect = self.rect()
                    widget_width, widget_height = widget_rect.width(), widget_rect.height()

                    scale_x = pdf_width / widget_width
                    scale_y = pdf_height / widget_height
                    scale = min(scale_x, scale_y) * self.controller.scale_config.scale_factor

                    painter.resetTransform()
                    painter.scale(scale, scale)

                    # Center content
                    x_offset = (pdf_width / scale - widget_width) / 2
                    y_offset = (pdf_height / scale - widget_height) / 2
                    painter.translate(x_offset, y_offset)

                    self.render(painter, QPoint(), QRegion(), QWidget.RenderFlag.DrawChildren)

                    if page < total_pages:
                        printer.newPage()

                painter.end()
                self.controller.navigate_to_page(original_page)
                QMessageBox.information(self, "چاپ", "فاکتور با موفقیت چاپ شد.")

            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در چاپ: {str(e)}")
                if painter.isActive():
                    painter.end()

    # Utility methods
    def _clear_table_selection(self):
        """Clear table selection."""
        if hasattr(self.ui, 'tableWidget1'):
            self.ui.tableWidget1.clearSelection()

    @contextmanager
    def _temporary_hide_footer(self):
        """Context manager to temporarily hide footer elements."""
        # Store original visibility states
        elements = ['pages_gb', 'footer_gb']
        original_states = {}

        for element_name in elements:
            if hasattr(self.ui, element_name):
                element = getattr(self.ui, element_name)
                original_states[element_name] = element.isVisible()
                element.setVisible(False)

        try:
            yield
        finally:
            # Restore original states
            for element_name, was_visible in original_states.items():
                if hasattr(self.ui, element_name):
                    element = getattr(self.ui, element_name)
                    element.setVisible(was_visible)

    def _to_persian_number(self, text: str) -> str:
        """Convert English digits to Persian digits."""
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        english_digits = '0123456789'

        for eng, per in zip(english_digits, persian_digits):
            text = text.replace(eng, per)

        return text

    def _show_error_message(self, message: str):
        """Show error message to user."""
        QMessageBox.critical(self, "خطا", message)

    def _show_success_message(self, message: str):
        """Show success message to user."""
        QMessageBox.information(self, "موفقیت", message)

    def _on_export_completed(self, file_path: str):
        """Handle export completed signal."""
        # You can add additional logic here if needed
        pass

    # Event handlers
    def keyPressEvent(self, event):
        """Handle key press events for navigation shortcuts."""
        if event.key() == Qt.Key.Key_Right or event.key() == Qt.Key.Key_PageDown:
            self.controller.next_page()
        elif event.key() == Qt.Key.Key_Left or event.key() == Qt.Key.Key_PageUp:
            self.controller.previous_page()
        elif event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_S:
                self._on_save_clicked()
            elif event.key() == Qt.Key.Key_P:
                self._on_print_clicked()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        self._adjust_table_columns()

    def closeEvent(self, event):
        """Handle dialog close event."""
        # Save current settings
        if hasattr(self, 'settings'):
            settings = QSettings("MyCompany", "InvoiceApp")
            settings.setValue("geometry", self.saveGeometry())

        event.accept()

    # Font management
    def set_text_edit_font_size(self):
        """Set font size for text edit widget."""
        if not hasattr(self.ui, 'textEdit'):
            return

        if self.ui.textEdit.toPlainText().strip():
            return

        font = QFont()
        font.setPointSize(self.controller.scale_config.remarks_font)
        self.ui.textEdit.setFont(font)

        char_format = QTextCharFormat()
        char_format.setFont(font)

        cursor = self.ui.textEdit.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.mergeCharFormat(char_format)
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.ui.textEdit.setTextCursor(cursor)