# -*- coding: utf-8 -*-

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPalette
from PySide6.QtWidgets import (QWidget, QTableWidgetItem, QCompleter, QMessageBox, QDialog, QApplication)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from shared import return_resource, get_persian_date, to_persian_number, render_colored_svg

# Import your models
from features.InvoicePage import DatabaseManager, InvoiceBackend

# Dictionary mapping SQLite error messages to Persian translations
SQLITE_ERROR_TRANSLATIONS = {
    "UNIQUE constraint failed": "خطای یکتایی: داده تکراری مجاز نیست.",
    "NOT NULL constraint failed": "خطای مقدار خالی: این فیلد اجباری است.",
    "FOREIGN KEY constraint failed": "خطای کلید خارجی: داده مرتبط وجود ندارد.",
    "no such table": "جدول مورد نظر وجود ندارد.",
    "no such column": "ستون مورد نظر وجود ندارد.",
    "database is locked": "پایگاه داده قفل شده است. لطفاً بعداً تلاش کنید.",
    "syntax error": "خطای دستوری در کوئری SQL.",
    "near": "خطای دستوری در بخشی از کوئری",
    "permission denied": "دسترسی به پایگاه داده مجاز نیست.",
    "disk I/O error": "خطای خواندن/نوشتن روی دیسک.",
}


def translate_sqlite_error(error):
    """Translate SQLite error messages to Persian."""
    error_str = str(error)
    for key, translation in SQLITE_ERROR_TRANSLATIONS.items():
        if key in error_str:
            return translation
    return f"خطای ناشناخته پایگاه داده: {error_str}"


class ValidationService:
    """Service for validating customer and invoice data."""

    def validate_customer_data(self, name, phone, national_id, address):
        """Validate customer data and return dict of errors."""
        errors = {}

        if not name or len(name.strip()) < 2:
            errors['name'] = "نام باید حداقل 2 کاراکتر باشد."

        if not phone or len(phone.strip()) < 10:
            errors['phone'] = "شماره تلفن باید حداقل 10 رقم باشد."

        if not national_id or len(national_id.strip()) != 10:
            errors['national_id'] = "کد ملی باید دقیقاً 10 رقم باشد."

        if not address or len(address.strip()) < 5:
            errors['address'] = "آدرس باید حداقل 5 کاراکتر باشد."

        return errors


class SubstringCompleter(QCompleter):
    def __init__(self, items, parent=None):
        super().__init__(items, parent)
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterMode(Qt.MatchContains)


class InvoicePage(QWidget):
    def __init__(self, parent, app_settings, user_context):
        super().__init__(parent)

        # Initialize UI
        from features.InvoicePage import InvoicePageUI
        self.ui = InvoicePageUI()
        self.ui.setupUi(self)

        # Initialize backend services
        self._setup_backend()

        # Initialize UI components
        self._setup_ui()
        self._setup_connections()
        self._setup_styling()

        # Initialize data
        self.current_date = get_persian_date()
        self.invoice_no = self.backend.get_current_invoice_number()

        # Load app settings
        from features.Settings import AppSettings
        self.app_settings = AppSettings()

    def _setup_backend(self):
        """Initialize backend services."""
        # Get database paths
        invoices_database = return_resource("databases", "invoices.db")
        customers_database = return_resource("databases", "customers.db")
        services_database = return_resource("databases", "services.db")  # Changed from documents to services

        # Initialize database manager and backend
        self.db_manager = DatabaseManager(customers_database, invoices_database, services_database)
        self.backend = InvoiceBackend(self.db_manager)
        self.validator = ValidationService()

    def _setup_ui(self):
        """Setup UI components."""
        # Set tab order
        QWidget.setTabOrder(self.ui.national_id_le, self.ui.full_name_le)
        QWidget.setTabOrder(self.ui.full_name_le, self.ui.phone_le)
        QWidget.setTabOrder(self.ui.phone_le, self.ui.address_le)

        # Set icons
        self.set_icons()

        # Setup autosuggestions
        self.setup_customer_autosuggestions()
        self.setup_document_autosuggestions()

        # Set horizontal scrollbar inactive
        self.ui.tableWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def _setup_connections(self):
        """Setup signal-slot connections."""
        # Customer buttons
        self.ui.invoice_button_add_customer.clicked.connect(self.save_customer)
        self.ui.invoice_button_delete_customer.clicked.connect(self.delete_customer)
        self.ui.invoice_button_customer_affairs.clicked.connect(self.show_customer_widget)

        # Customer field autofill
        self.ui.full_name_le.textChanged.connect(lambda: self.autofill_data("name", self.ui.full_name_le.text()))
        self.ui.phone_le.textChanged.connect(lambda: self.autofill_data("phone", self.ui.phone_le.text()))
        self.ui.national_id_le.textChanged.connect(
            lambda: self.autofill_data("national_id", self.ui.national_id_le.text()))

        # Document buttons
        self.ui.add_document_to_invoice_button.clicked.connect(self.show_price_window)
        self.ui.documents_le.returnPressed.connect(self.show_price_window)

        # Invoice buttons
        self.ui.preview_invoice_button.clicked.connect(self.show_invoice_preview)
        self.ui.clear_table_button.clicked.connect(self.clear_table)
        self.ui.delete_item_button.clicked.connect(self.delete_item)
        self.ui.edit_item_button.clicked.connect(self.edit_item)

    def _setup_styling(self):
        """Setup widget styling."""
        self.setStyleSheet("""
            QGroupBox {
                background-color: palette(window);
                border: 1px solid palette(mid);
                border-radius: 6px;
                margin-top: 20px;
                padding-left: 20px;
                padding-right: 20px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 8px;
                color: palette(windowText);
                background-color: transparent;
                font-weight: bold;
            }

            #customer_gb QLabel{
                color: palette(windowText);
                QPushButton: color{palette(base)}
            }

            #documents_section QLabel{
                color: palette(windowText);
            }

            QLineEdit {
                background-color: palette(base);
                color: palette(text);
                border: 1px solid palette(mid);
                border-radius: 4px;
                padding: 4px;
            }

            QLineEdit:focus {
                border: 1px solid palette(link);
            }
        """)

    def set_icons(self):
        """Set icons for buttons."""
        base_color = QApplication.instance().palette().color(QPalette.Highlight).name()

        # Load icon resources
        add_user_icon = return_resource("resources", "add-user.svg", "icons")
        remove_user_icon = return_resource("resources", "remove-user.svg", "icons")
        users_icon = return_resource("resources", "user-group.svg", "icons")
        add_document_icon = return_resource("resources","add-document.svg", "icons")

        # Create and set icons
        add_user_pixmap = render_colored_svg(add_user_icon, QSize(45, 45), base_color)
        self.ui.invoice_button_add_customer.setIcon(QIcon(add_user_pixmap))
        self.ui.invoice_button_add_customer.setIconSize(QSize(45, 45))

        remove_user_pixmap = render_colored_svg(remove_user_icon, QSize(45, 45), base_color)
        self.ui.invoice_button_delete_customer.setIcon(QIcon(remove_user_pixmap))
        self.ui.invoice_button_delete_customer.setIconSize(QSize(45, 45))

        users_pixmap = render_colored_svg(users_icon, QSize(45, 45), base_color)
        self.ui.invoice_button_customer_affairs.setIcon(QIcon(users_pixmap))
        self.ui.invoice_button_customer_affairs.setIconSize(QSize(45, 45))

        add_document_pixmap = render_colored_svg(add_document_icon, QSize(60, 60), base_color)
        self.ui.add_document_to_invoice_button.setIcon(QIcon(add_document_pixmap))
        self.ui.add_document_to_invoice_button.setIconSize(QSize(60, 60))

    # Customer Management Methods
    def setup_customer_autosuggestions(self):
        """Set up QCompleter for customer fields."""
        fields = {
            "name": self.ui.full_name_le,
            "phone": self.ui.phone_le,
            "national_id": self.ui.national_id_le,
        }

        for field_name, line_edit in fields.items():
            suggestions = self.backend.get_customer_suggestions(field_name)
            completer = QCompleter(suggestions)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.activated.connect(lambda value, field=field_name: self.autofill_data(field, value))
            line_edit.setCompleter(completer)

    def autofill_data(self, field_name, value):
        """Autofill customer data when a value is selected."""
        if field_name == "name":
            customer = self.backend.get_customer_by_name(value)
        elif field_name == "phone":
            customer = self.backend.get_customer_by_phone(value)
        elif field_name == "national_id":
            customer = self.backend.get_customer_by_national_id(value)
        else:
            return

        if customer:
            self.ui.full_name_le.setText(customer.name)
            self.ui.phone_le.setText(customer.phone)
            self.ui.national_id_le.setText(customer.national_id)
            self.ui.address_le.setText(customer.address or "")

    def validate_customer(self):
        """Validate customer input fields."""
        name = self.ui.full_name_le.text().strip()
        phone = self.ui.phone_le.text().strip()
        national_id = self.ui.national_id_le.text().strip()
        address = self.ui.address_le.text().strip()

        # Clear previous errors
        self.clear_validation_errors()

        # Validate using backend service
        errors = self.validator.validate_customer_data(name, phone, national_id, address)

        if errors:
            for field, error_message in errors.items():
                if field == "name":
                    self.show_field_error(self.ui.full_name_le, error_message)
                elif field == "phone":
                    self.show_field_error(self.ui.phone_le, error_message)
                elif field == "national_id":
                    self.show_field_error(self.ui.national_id_le, error_message)
                elif field == "address":
                    self.show_field_error(self.ui.address_le, error_message)
            return False

        return True

    def save_customer(self):
        """Save customer data to database."""
        if not self.validate_customer():
            return

        name = self.ui.full_name_le.text().strip()
        phone = self.ui.phone_le.text().strip()
        national_id = self.ui.national_id_le.text().strip()
        address = self.ui.address_le.text().strip()

        success, message = self.backend.save_customer(national_id, name, phone, address)

        if success:
            self.clear_customer_fields()
            self.setup_customer_autosuggestions()
            self.show_custom_message("information", "موفقیت", "مشتری با موفقیت ذخیره شد.")
        else:
            error_message = translate_sqlite_error(message)
            self.show_custom_message("warning", "خطا", error_message)

    def delete_customer(self):
        """Delete customer from database."""
        national_id = self.ui.national_id_le.text().strip()

        if not national_id:
            self.show_custom_message("warning", "خطا", "لطفاً کد ملی مشتری را وارد کنید.")
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "تایید حذف",
            f"آیا از حذف مشتری با کد ملی {national_id} اطمینان دارید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.backend.delete_customer(national_id)

            if success:
                self.clear_customer_fields()
                self.setup_customer_autosuggestions()
                self.show_custom_message("information", "موفقیت", "مشتری با موفقیت حذف شد.")
            else:
                error_message = translate_sqlite_error(message)
                self.show_custom_message("warning", "خطا", error_message)

    def clear_customer_fields(self):
        """Clear all customer input fields."""
        self.ui.full_name_le.clear()
        self.ui.phone_le.clear()
        self.ui.national_id_le.clear()
        self.ui.address_le.clear()

    def show_customer_widget(self):
        """Show customer management widget."""
        try:
            from modules.Customer.customer_widget import CustomerWidget
            self.customer_widget = CustomerWidget(self)
            self.customer_widget.show()
        except ImportError as e:
            self.show_custom_message("warning", "خطا", f"خطا در بارگذاری صفحه مشتریان: {str(e)}")

    # Document Management Methods
    def setup_document_autosuggestions(self):
        """Set up QCompleter for document field."""
        documents = self.backend.get_all_services()
        document_names = [doc['name'] for doc in documents]

        completer = SubstringCompleter(document_names, self)
        self.ui.documents_le.setCompleter(completer)

    def show_price_window(self):
        """Show price input window for selected document."""
        document_name = self.ui.documents_le.text().strip()

        if not document_name:
            self.show_custom_message("warning", "خطا", "لطفاً نام سند را وارد کنید.")
            return

        # Check if document exists
        document = self.backend.get_document_by_name(document_name)
        if not document:
            self.show_custom_message("warning", "خطا", "سند مورد نظر در پایگاه داده موجود نیست.")
            return

        # Show price input dialog
        from modules.Invoice.price_dialog import PriceDialog
        dialog = PriceDialog(self, document)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            price = dialog.get_price()
            count = dialog.get_count()

            if price and count:
                self.add_document_to_invoice(document, price, count)
                self.ui.documents_le.clear()

    def add_document_to_invoice(self, document, price, count):
        """Add document to invoice table."""
        try:
            # Calculate total price
            total_price = float(price) * int(count)

            # Add row to table
            row_position = self.ui.tableWidget.rowCount()
            self.ui.tableWidget.insertRow(row_position)

            # Set table items
            self.ui.tableWidget.setItem(row_position, 0, QTableWidgetItem(str(row_position + 1)))
            self.ui.tableWidget.setItem(row_position, 1, QTableWidgetItem(document['name']))
            self.ui.tableWidget.setItem(row_position, 2, QTableWidgetItem(to_persian_number(str(count))))
            self.ui.tableWidget.setItem(row_position, 3, QTableWidgetItem(to_persian_number(str(price))))
            self.ui.tableWidget.setItem(row_position, 4, QTableWidgetItem(to_persian_number(str(total_price))))

            # Store document ID in first column for later use
            self.ui.tableWidget.item(row_position, 0).setData(Qt.ItemDataRole.UserRole, document['id'])

            # Update total amount
            self.update_total_amount()

        except (ValueError, TypeError) as e:
            self.show_custom_message("warning", "خطا", f"خطا در افزودن سند: {str(e)}")

    def update_total_amount(self):
        """Update total amount label."""
        total = 0
        for row in range(self.ui.tableWidget.rowCount()):
            amount_item = self.ui.tableWidget.item(row, 4)
            if amount_item:
                try:
                    # Convert Persian numbers back to English for calculation
                    amount_text = amount_item.text()
                    # Simple Persian to English number conversion
                    persian_to_english = {
                        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
                        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
                    }
                    for p, e in persian_to_english.items():
                        amount_text = amount_text.replace(p, e)

                    total += float(amount_text)
                except (ValueError, TypeError):
                    continue

        self.ui.total_amount_label.setText(f"مجموع: {to_persian_number(str(total))} تومان")

    def delete_item(self):
        """Delete selected item from invoice table."""
        current_row = self.ui.tableWidget.currentRow()

        if current_row < 0:
            self.show_custom_message("warning", "خطا", "لطفاً ردیف مورد نظر را انتخاب کنید.")
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "تایید حذف",
            "آیا از حذف این آیتم اطمینان دارید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.ui.tableWidget.removeRow(current_row)
            self.update_row_numbers()
            self.update_total_amount()

    def edit_item(self):
        """Edit selected item in invoice table."""
        current_row = self.ui.tableWidget.currentRow()

        if current_row < 0:
            self.show_custom_message("warning", "خطا", "لطفاً ردیف مورد نظر را انتخاب کنید.")
            return

        # Get current item data
        document_name = self.ui.tableWidget.item(current_row, 1).text()
        current_count = self.ui.tableWidget.item(current_row, 2).text()
        current_price = self.ui.tableWidget.item(current_row, 3).text()
        document_id = self.ui.tableWidget.item(current_row, 0).data(Qt.ItemDataRole.UserRole)

        # Get document data
        document = self.backend.get_document_by_id(document_id)
        if not document:
            self.show_custom_message("warning", "خطا", "سند مورد نظر یافت نشد.")
            return

        # Show edit dialog
        from modules.Invoice.price_dialog import PriceDialog
        dialog = PriceDialog(self, document)

        # Set current values
        dialog.set_price(self._convert_persian_to_english(current_price))
        dialog.set_count(self._convert_persian_to_english(current_count))

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_price = dialog.get_price()
            new_count = dialog.get_count()

            if new_price and new_count:
                # Update table items
                total_price = float(new_price) * int(new_count)

                self.ui.tableWidget.setItem(current_row, 2, QTableWidgetItem(to_persian_number(str(new_count))))
                self.ui.tableWidget.setItem(current_row, 3, QTableWidgetItem(to_persian_number(str(new_price))))
                self.ui.tableWidget.setItem(current_row, 4, QTableWidgetItem(to_persian_number(str(total_price))))

                self.update_total_amount()

    def clear_table(self):
        """Clear all items from invoice table."""
        if self.ui.tableWidget.rowCount() == 0:
            self.show_custom_message("information", "اطلاعات", "جدول خالی است.")
            return

        reply = QMessageBox.question(
            self,
            "تایید پاک کردن",
            "آیا از پاک کردن تمام آیتم‌های جدول اطمینان دارید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.ui.tableWidget.setRowCount(0)
            self.update_total_amount()

    def update_row_numbers(self):
        """Update row numbers after deletion."""
        for row in range(self.ui.tableWidget.rowCount()):
            self.ui.tableWidget.setItem(row, 0, QTableWidgetItem(str(row + 1)))

    # Invoice Management Methods
    def show_invoice_preview(self):
        """Show invoice preview window."""
        if not self.validate_invoice_data():
            return

        # Prepare invoice data
        invoice_data = self.prepare_invoice_data()

        # Show preview window
        try:
            from modules.Invoice.invoice_preview import InvoicePreview
            self.invoice_preview = InvoicePreview(self, invoice_data)
            self.invoice_preview.show()
        except ImportError as e:
            self.show_custom_message("warning", "خطا", f"خطا در بارگذاری پیش‌نمایش فاکتور: {str(e)}")

    def validate_invoice_data(self):
        """Validate invoice data before saving or preview."""
        # Check customer data
        if not self.ui.full_name_le.text().strip():
            self.show_custom_message("warning", "خطا", "لطفاً نام مشتری را وارد کنید.")
            return False

        if not self.ui.national_id_le.text().strip():
            self.show_custom_message("warning", "خطا", "لطفاً کد ملی مشتری را وارد کنید.")
            return False

        if not self.ui.phone_le.text().strip():
            self.show_custom_message("warning", "خطا", "لطفاً شماره تلفن مشتری را وارد کنید.")
            return False

        # Check if table has items
        if self.ui.tableWidget.rowCount() == 0:
            self.show_custom_message("warning", "خطا", "لطفاً حداقل یک آیتم به فاکتور اضافه کنید.")
            return False

        return True

    def prepare_invoice_data(self):
        """Prepare invoice data for saving or preview."""
        # Get customer data
        customer_data = {
            'name': self.ui.full_name_le.text().strip(),
            'national_id': self.ui.national_id_le.text().strip(),
            'phone': self.ui.phone_le.text().strip(),
            'address': self.ui.address_le.text().strip()
        }

        # Get invoice items
        items = []
        for row in range(self.ui.tableWidget.rowCount()):
            document_name = self.ui.tableWidget.item(row, 1).text()
            count = self.ui.tableWidget.item(row, 2).text()
            price = self.ui.tableWidget.item(row, 3).text()
            total = self.ui.tableWidget.item(row, 4).text()
            document_id = self.ui.tableWidget.item(row, 0).data(Qt.ItemDataRole.UserRole)

            items.append({
                'document_id': document_id,
                'document_name': document_name,
                'count': count,
                'price': price,
                'total': total
            })

        # Calculate total amount
        total_amount = 0
        for item in items:
            try:
                # Convert Persian numbers to English for calculation
                total_text = self._convert_persian_to_english(item['total'])
                total_amount += float(total_text)
            except (ValueError, TypeError):
                continue

        return {
            'invoice_number': self.invoice_no,
            'date': self.current_date,
            'customer': customer_data,
            'items': items,
            'total_amount': total_amount
        }

    def save_invoice(self):
        """Save invoice to database."""
        if not self.validate_invoice_data():
            return

        invoice_data = self.prepare_invoice_data()
        success, message = self.backend.save_invoice(invoice_data)

        if success:
            self.show_custom_message("information", "موفقیت", "فاکتور با موفقیت ذخیره شد.")
            self.clear_invoice_form()
            self.invoice_no = self.backend.get_current_invoice_number()
        else:
            error_message = translate_sqlite_error(message)
            self.show_custom_message("warning", "خطا", error_message)

    def clear_invoice_form(self):
        """Clear all invoice form fields."""
        self.clear_customer_fields()
        self.ui.tableWidget.setRowCount(0)
        self.ui.documents_le.clear()
        self.update_total_amount()

    # Utility Methods
    def show_field_error(self, field, message):
        """Show error styling for a field."""
        field.setStyleSheet("""
            QLineEdit {
                border: 2px solid red;
                background-color: #ffe6e6;
            }
        """)
        field.setToolTip(message)

    def clear_validation_errors(self):
        """Clear validation error styling from all fields."""
        fields = [
            self.ui.full_name_le,
            self.ui.phone_le,
            self.ui.national_id_le,
            self.ui.address_le
        ]

        for field in fields:
            field.setStyleSheet("")
            field.setToolTip("")

    def show_custom_message(self, icon_type, title, message):
        """Show custom message box."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)

        if icon_type == "information":
            msg_box.setIcon(QMessageBox.Icon.Information)
        elif icon_type == "warning":
            msg_box.setIcon(QMessageBox.Icon.Warning)
        elif icon_type == "critical":
            msg_box.setIcon(QMessageBox.Icon.Critical)

        msg_box.exec()

    def _convert_persian_to_english(self, text):
        """Convert Persian numbers to English."""
        if not text:
            return text

        persian_to_english = {
            '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
            '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
        }

        result = text
        for p, e in persian_to_english.items():
            result = result.replace(p, e)

        return result

    def closeEvent(self, event):
        """Handle window close event."""
        # Clean up database connections
        if hasattr(self, 'db_manager'):
            self.db_manager.close_all_connections()

        event.accept()

    def keyPressEvent(self, event):
        """Handle key press events."""
        # Add keyboard shortcuts
        if event.key() == Qt.Key.Key_F5:
            self.show_invoice_preview()
        elif event.key() == Qt.Key.Key_F2:
            self.save_invoice()
        elif event.key() == Qt.Key.Key_Delete:
            self.delete_item()
        elif event.key() == Qt.Key.Key_Escape:
            self.clear_invoice_form()

        super().keyPressEvent(event)
