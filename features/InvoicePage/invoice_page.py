# -*- coding: utf-8 -*-

import sqlite3

from modules.helper_functions import return_resource, get_persian_date, render_colored_svg, to_persian_number
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPalette
from PySide6.QtWidgets import (QWidget, QTableWidgetItem, QCompleter, QMessageBox, QDialog)

from modules.user_context import UserContext



# Dictionary mapping SQLite error messages to Persian translations
SQLITE_ERROR_TRANSLATIONS = {
    # Common constraint errors
    "UNIQUE constraint failed": "خطای یکتایی: داده تکراری مجاز نیست.",
    "NOT NULL constraint failed": "خطای مقدار خالی: این فیلد اجباری است.",
    "FOREIGN KEY constraint failed": "خطای کلید خارجی: داده مرتبط وجود ندارد.",

    # Table/database errors
    "no such table": "جدول مورد نظر وجود ندارد.",
    "no such column": "ستون مورد نظر وجود ندارد.",
    "database is locked": "پایگاه داده قفل شده است. لطفاً بعداً تلاش کنید.",

    # Syntax/query errors
    "syntax error": "خطای دستوری در کوئری SQL.",
    "near": "خطای دستوری در بخشی از کوئری",

    # General errors
    "permission denied": "دسترسی به پایگاه داده مجاز نیست.",
    "disk I/O error": "خطای خواندن/نوشتن روی دیسک.",
}


def translate_sqlite_error(error):
    """Translate SQLite error messages to Persian."""
    error_str = str(error)

    # Check for matching error patterns
    for key, translation in SQLITE_ERROR_TRANSLATIONS.items():
        if key in error_str:
            return translation

    # Fallback for untranslated errors
    return f"خطای ناشناخته پایگاه داده: {error_str}"  # "Unknown database error"


invoices_database = return_resource("databases", "invoices.db")
customers_database = return_resource("databases", "customers.db")
documents_database = return_resource("databases", "documents.db")

add_user_icon = return_resource(folder1="resources",folder2="icons", resource="add-user.svg")
remove_user_icon = return_resource(folder1="resources", folder2="icons", resource="remove-user.svg")
users_icon = return_resource(folder1="resources", folder2="icons", resource="user-group.svg")
add_document_icon = return_resource(folder1="resources", folder2="icons", resource="add-document.svg")


class SubstringCompleter(QCompleter):
    def __init__(self, items, parent=None):
        super().__init__(items, parent)
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterMode(Qt.MatchContains)


class InvoicePage(QWidget):

    def __init__(self, parent):  # user_context: UserContext
        super().__init__(parent)

        from qt_designer_ui.ui_invoice_widget import Ui_page_invoice
        self.ui = Ui_page_invoice()
        self.ui.setupUi(self)

        # self.user_context = user_context

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
                color: palette(windowText);  /* Color changes according to theme */
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

            /* Optional: Style QLineEdit focus behavior */
            QLineEdit:focus {
                border: 1px solid palette(link);
            }
        """)
        # with open("styles/invoice_page_styles.qss", "r") as f:
        #     self.setStyleSheet(f.read())

        QWidget.setTabOrder(self.ui.national_id_le, self.ui.full_name_le)
        QWidget.setTabOrder(self.ui.full_name_le, self.ui.phone_le)
        QWidget.setTabOrder(self.ui.phone_le, self.ui.address_le)

        # Set icon pixmaps
        self.set_icons()

        # Setup autosuggestion
        self.setup_customer_autosuggestions()
        self.ui.invoice_button_add_customer.clicked.connect(self.save_customer)
        self.ui.invoice_button_delete_customer.clicked.connect(self.delete_customer)

        # Buttons
        self.ui.invoice_button_customer_affairs.clicked.connect(self.show_customer_widget)

        # Connect signals for autofill
        self.ui.full_name_le.textChanged.connect(lambda: self.autofill_data("name", self.ui.full_name_le.text()))
        self.ui.phone_le.textChanged.connect(lambda: self.autofill_data("phone", self.ui.phone_le.text()))
        self.ui.national_id_le.textChanged.connect(
            lambda: self.autofill_data("national_id", self.ui.national_id_le.text()))

        self.current_date = get_persian_date()

        self.setup_document_autosuggestions()
        self.ui.add_document_to_invoice_button.clicked.connect(self.show_price_window)
        self.ui.documents_le.returnPressed.connect(self.show_price_window)
        self.ui.preview_invoice_button.clicked.connect(self.show_invoice_preview)
        self.ui.clear_table_button.clicked.connect(self.clear_table)
        self.ui.delete_item_button.clicked.connect(self.delete_item)
        self.ui.edit_item_button.clicked.connect(self.edit_item)

        self.invoice_no = self.get_current_invoice_no()

        # Set the horizontal scrollbar inactive
        self.ui.tableWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        from modules.Settings.app_settings import AppSettings
        self.app_settings = AppSettings()

    def set_icons(self):
        """changes current button icons to generated svg icons."""
        from PySide6.QtWidgets import QApplication
        base_color = QApplication.instance().palette().color(QPalette.Highlight).name()

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

    def show_customer_widget(self):
        from modules.InvoicePage.customer_page import CustomerTable

        self.customer_affairs = CustomerTable()
        self.customer_affairs.show()

        self.customer_affairs.raise_()
        self.customer_affairs.activateWindow()

    def clear_table(self):
        """clears the table"""
        self.ui.tableWidget.setRowCount(0)

    def show_price_window(self):
        """Show an instance of the PriceWindow dialog."""
        from modules.InvoicePage import PriceWindow
        document_name = self.get_document_name()
        price_window = PriceWindow(self, document_name)
        validated_document_name = self.validate_document_name()

        if not document_name:
            self.show_custom_message("warning", "خطا", "لطفا مدرک مورد نظر را وارد کنید!")
            return

        if validated_document_name is None:
            self.show_custom_message("warning", "خطا", "این مدرک در پایگاه داده وجود ندارد!")
            return

        if document_name == "سایر خدمات" or document_name == "امور خارجه":
            self.add_other_documents_to_invoice()
            return

        if price_window.exec() == QDialog.Accepted:
            pass

    def show_invoice_preview(self):

        from modules.InvoicePage.invoice_preview import InvoicePreview
        invoice_preview = InvoicePreview(parent_invoice_widget=self,
                                         app_settings=self.app_settings)  # user_context=self.user_context

        if self.validate_customer() == 1:
            pass
        else:
            return  # Ensures the customer fields are filled correctly

        if invoice_preview.exec() == QDialog.Accepted:
            pass
        else:
            pass

    def delete_item(self):
        """Delete the selected customer from the database."""
        selected_row = self.ui.tableWidget.currentRow()
        if selected_row == -1:
            return

        item = self.ui.tableWidget.item(selected_row, 0)
        value = item.text() if item is not None else ""

        reply = QMessageBox.question(
            self, "حذف مشتری", f"آیا مطمئن هستید که می‌خواهید {value} را حذف کنید؟",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.ui.tableWidget.removeRow(selected_row)

    def edit_item(self):
        """Opens PriceWindow dialog for the selected item, when the edit is done, it replaces the sai item."""
        # Step 1: select the item's row
        selected_row = self.ui.tableWidget.currentRow()
        if selected_row == -1:
            return

        # Step 2: Extract its document name
        item = self.ui.tableWidget.item(selected_row, 0)
        document_name = item.text() if item is not None else ""

        # Step 3: Open PriceWindow dialog for that document
        from modules.InvoicePage.price_window import PriceWindow
        price_window = PriceWindow(self, document_name, selected_row)

        if document_name == "سایر خدمات" or document_name == "امور خارجه":
            QMessageBox.warning(self, "توجه", "سایر خدمات و امور خارجه را می‌توانید در جدول ویرایش کنید.")
            return

        if price_window.exec() == QDialog.Accepted:
            pass

    def add_other_documents_to_invoice(self):
        # Find the first available row
        document_name = self.ui.documents_le.text()
        row_count = self.ui.tableWidget.rowCount()
        self.ui.tableWidget.insertRow(row_count)
        base_price = self.calculate_base_price(document_name)

        # Add document name
        document_item = QTableWidgetItem(document_name)
        document_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.ui.tableWidget.setItem(row_count, 0, document_item)

        # Official or unofficial
        document_official = QTableWidgetItem("-")
        document_official.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.ui.tableWidget.setItem(row_count, 1, document_official)

        # Add document count
        item_count = QTableWidgetItem("-")
        self.ui.tableWidget.setItem(row_count, 2, item_count)

        # Add checkmark for judiciary seal
        judiciary_item = QTableWidgetItem("-")
        judiciary_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.ui.tableWidget.setItem(row_count, 3, judiciary_item)

        # Add checkmark for foreign affairs seal
        foreign_affairs_item = QTableWidgetItem("-")
        foreign_affairs_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.ui.tableWidget.setItem(row_count, 4, foreign_affairs_item)

        # Add total price
        total_price_item = QTableWidgetItem(f"{base_price}")
        self.ui.tableWidget.setItem(row_count, 5, total_price_item)

        # Add remarks
        remarks = QTableWidgetItem("")
        self.ui.tableWidget.setItem(row_count, 6, remarks)

        # Remove the last additional column until I debug it
        self.ui.tableWidget.removeColumn(7)

        self.update_row_numbers()
        self.clear_document_fields()

    def setup_document_autosuggestions(self):
        """Fetch all document names from the database."""
        with sqlite3.connect(documents_database) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM Services")
            services = [row[0] for row in cursor.fetchall()]

        # Use customized completer method
        all_services = services
        completer = SubstringCompleter(all_services, self.ui.documents_le)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.ui.documents_le.setCompleter(completer)

    def get_dynamic_price_1(self, document_name):
        """Retrieves the 1st dynamic price from database."""
        # Connect to the database
        conn = sqlite3.connect(documents_database)
        cursor = conn.cursor()

        try:
            # Fetch dynamic_price_1 from the specified row
            cursor.execute("SELECT dynamic_price_1 FROM Services WHERE name = ?", (document_name,))
            result = cursor.fetchone()  # Fetch the row

            if result:
                dynamic_price_1 = result[0]
                return dynamic_price_1
            if not result:
                return None

        except sqlite3.Error as e:
            self.show_custom_message("critical", "خطای پایگاه داده", f"{translate_sqlite_error(e)}")
            return None

        finally:
            conn.close()

    def get_dynamic_price_2(self, document_name):
        """Retrieves the 2nd dynamic price from database."""
        # Connect to the database
        conn = sqlite3.connect(documents_database)
        cursor = conn.cursor()

        try:
            # Fetch dynamic_price_2 from the specified row
            cursor.execute("SELECT dynamic_price_2 FROM Services WHERE name = ?", (document_name,))
            result = cursor.fetchone()  # Fetch the row

            if result:
                dynamic_price_2 = result[0]
                return dynamic_price_2
            if not result:
                return None

        except sqlite3.Error as e:
            self.show_custom_message("critical", "خطای پایگاه داده", f"{translate_sqlite_error(e)}")
            return None

        finally:
            conn.close()

    def get_document_name(self):
        """Returns the document name from document_le"""
        return self.ui.documents_le.text().strip()

    def validate_document_name(self):
        """
        Check if the provided document_name exists in the 'services' table.
        If it exists, returns associated name; otherwise, return None.
        """
        document_name = self.get_document_name()
        connection = sqlite3.connect(documents_database)
        cursor = connection.cursor()

        query = """
        SELECT name FROM services WHERE name = ?
        """
        cursor.execute(query, (document_name,))
        result = cursor.fetchone()
        connection.close()

        if result:
            return result
        else:
            return None

    def calculate_base_price(self, document_name):
        conn = sqlite3.connect(documents_database)
        cursor = conn.cursor()

        # Check if the document is in Services
        cursor.execute("SELECT base_price FROM Services WHERE name = ?", (document_name,))
        service = cursor.fetchone()
        if service:
            conn.close()
            return service[0]  # Base price for the service
        return 0  # Document not found in the database

    def update_row_numbers(self):
        """Update the vertical header labels to show Persian numerals."""
        row_count = self.ui.tableWidget.rowCount()
        persian_numbers = [to_persian_number(row + 1) for row in range(row_count)]
        self.ui.tableWidget.setVerticalHeaderLabels(persian_numbers)

    def keyPressEvent(self, event):
        """Override keyPressEvent to handle Tab key presses going  right to left instead of left to right."""
        if event.key() == Qt.Key_Tab:
            # Reverse Tab navigation
            self.focusPreviousChild()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        """Adjust column widths for both tables."""
        # Parent table widget configuration
        parent_column_widths = [40, 8, 6, 4, 4, 12, 23]
        parent_table_width = self.ui.tableWidget.width()
        self.ui.tableWidget.horizontalHeader().setStretchLastSection(False)
        for i, percentage in enumerate(parent_column_widths):
            self.ui.tableWidget.setColumnWidth(i, parent_table_width * percentage / 100)

        super().resizeEvent(event)  # Ensure the base class implementation is called

    def clear_validation_errors(self):
        """Remove all validation error styles and messages."""
        for line_edit in [self.ui.full_name_le, self.ui.phone_le, self.ui.national_id_le, self.ui.address_le]:
            line_edit.setStyleSheet("")  # Reset border
            if hasattr(line_edit, "error_label") and line_edit.error_label:
                line_edit.error_label.hide()  # Hide error label

    def validate_customer(self):
        """Validate input fields and highlight errors instead of blocking UI."""

        # Retrieve and normalize input values
        name = self.ui.full_name_le.text().strip()
        phone = self.ui.phone_le.text().strip()
        national_id = self.ui.national_id_le.text().strip()
        address = self.ui.address_le.text().strip()

        # Remove previous error styles and messages
        self.clear_validation_errors()

        errors = []  # Store which fields have errors

        # Validation rules
        if not name:
            self.show_field_error(self.ui.full_name_le, "نام مشتری نباید خالی باشد.")
            errors.append(self.ui.full_name_le)

        if not (phone.isdigit() and 10 <= len(phone) <= 11):
            self.show_field_error(self.ui.phone_le, "شماره تلفن مشتری باید ۱۰ تا ۱۱ رقم باشد.")
            errors.append(self.ui.phone_le)

        if not (national_id.isdigit() and len(national_id) == 10):
            self.show_field_error(self.ui.national_id_le, "کد ملی مشتری باید ۱۰ رقم باشد.")
            errors.append(self.ui.national_id_le)

        if not address:
            self.show_field_error(self.ui.address_le, "آدرس مشتری نباید خالی باشد.")
            errors.append(self.ui.address_le)

        if errors:
            return  # Stop processing if there are errors

        return 1  # All inputs are valid

    def setup_customer_autosuggestions(self):
        """Set up QCompleter for all line edits."""
        fields = {
            "name": self.ui.full_name_le,
            "phone": self.ui.phone_le,
            "national_id": self.ui.national_id_le,
        }

        try:
            conn = sqlite3.connect(customers_database)
            cursor = conn.cursor()

            for field_name, line_edit in fields.items():
                # Fetch unique values for the field
                cursor.execute(f"SELECT DISTINCT {field_name} FROM customers")
                suggestions = [row[0] for row in cursor.fetchall() if row[0]]

                # Set up QCompleter
                completer = QCompleter(suggestions)
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                completer.activated.connect(
                    lambda value, field=field_name: self.autofill_data(field, value)
                )
                line_edit.setCompleter(completer)

            conn.close()
        except sqlite3.Error as e:
            self.show_custom_message("critical", "خطای پایگاه داده", f"{translate_sqlite_error(e)}")

    def autofill_data(self, field_name, value):
        """Autofill customer data when a value is selected from QCompleter."""
        conn = sqlite3.connect(customers_database)
        cursor = conn.cursor()

        # Query the database for the selected value
        query = f"SELECT name, phone, national_id, address FROM customers WHERE {field_name} = ?"
        cursor.execute(query, (value,))
        customer_data = cursor.fetchone()
        try:
            if customer_data:
                # Populate all fields with the retrieved data
                self.ui.full_name_le.setText(customer_data[0])
                self.ui.phone_le.setText(customer_data[1])
                self.ui.national_id_le.setText(customer_data[2])
                self.ui.address_le.setText(customer_data[3])

        except ValueError:
            self.show_custom_message("critical", "خطای پایگاه داده",
                                     "این مشتری در پایگاه داده وجود ندارد!")

        conn.close()

    def save_customer(self):
        """Validate input fields and save customer data."""
        # Retrieve and normalize input values
        name = self.ui.full_name_le.text().strip()
        phone = self.ui.phone_le.text().strip()
        national_id = self.ui.national_id_le.text().strip()
        address = self.ui.address_le.text().strip()

        # Validate customer input
        validation = self.validate_customer()
        if validation != 1:
            return  # The customer inputs are not valid

        # Save customer to the database
        try:
            conn = sqlite3.connect(customers_database)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO customers (national_id, name, phone, address)
                VALUES (?, ?, ?, ?)
            """, (national_id, name, phone, address))
            conn.commit()

            # Clear input fields and refresh UI components
            self.clear_customer_fields()
            self.setup_customer_autosuggestions()

            self.show_custom_message("information", "موفقیت", "مشتری با موفقیت ذخیره شد!")

        except sqlite3.IntegrityError as e:
            # Handle duplicate national ID or phone number
            if "UNIQUE constraint failed" in str(e):
                self.show_custom_message("warning", "خطای پایگاه داده", "کد ملی یا شماره تلفن تکراری است.")
            else:
                self.show_custom_message("critical", "خطای پایگاه داده", f"{translate_sqlite_error(e)}")
        except sqlite3.Error as e:
            self.show_custom_message("critical", "خطای پایگاه داده", f"{translate_sqlite_error(e)}")
        finally:
            if conn:
                conn.close()

    def delete_customer(self):
        """Delete a customer from the database."""
        # Retrieve the unique identifier for the customer (e.g., phone number or national ID)
        national_id = self.ui.national_id_le.text().strip()

        # Ensure the identifier is provided
        self.clear_validation_errors()

        if not national_id:
            self.show_field_error(self.ui.national_id_le, "لطفاً کد ملی مشتری را خالی نگذارید.")
            return

        # Delete the customer from the database
        try:
            conn = sqlite3.connect(customers_database)
            cursor = conn.cursor()

            # Fetch the customer's name
            cursor.execute("SELECT name FROM customers WHERE national_id = ?", (national_id,))
            customer = cursor.fetchone()

            if not customer:
                self.show_field_error(self.ui.national_id_le, "مشتری با این کد ملی پیدا نشد.")
                return

            customer_name = customer[0]

            # Confirm deletion
            reply = self.show_custom_message(
                "question",
                "تایید حذف",
                f"آیا مطمئن هستید که می‌خواهید {customer_name} را از لیست مشتریان حذف کنید؟",
                "بله", "خیر"
            )

            if reply.text() == "خیر":  # or check `if reply == cancel_button` if you store it
                return

            # Delete query
            cursor.execute("""
                DELETE FROM customers WHERE national_id = ?
            """, (national_id,))
            conn.commit()
            conn.close()

            # Check if the customer was deleted
            if cursor.rowcount == 0:
                self.show_field_error(self.ui.national_id_le, "مشتری با این کد ملی پیدا نشد.")
            else:
                self.show_custom_message("information", "موفقیت", "مشتری با موفقیت حذف شد!")

            # Clear fields and refresh suggestions
            self.clear_customer_fields()
            self.setup_customer_autosuggestions()
        except sqlite3.Error as e:
            self.show_custom_message("critical", "خطای پایگاه داده", f"{translate_sqlite_error(e)}")

    def clear_document_fields(self):
        """Clear document fields to enter new items."""
        # Reset checkboxes and clear input field
        self.ui.documents_le.clear()

    def clear_customer_fields(self):
        """Clear all input fields."""
        self.ui.full_name_le.clear()
        self.ui.phone_le.clear()
        self.ui.national_id_le.clear()
        self.ui.address_le.clear()

    def get_current_invoice_no(self):
        """
        Retrieve the latest invoice number from the database.
        Returns 1000 if no invoices exist.
        """
        with sqlite3.connect(invoices_database) as connection:
            cursor = connection.cursor()

            try:
                cursor.execute("SELECT MAX(invoice_number) FROM issued_invoices")
                last_invoice_number = cursor.fetchone()[0]

                return last_invoice_number if last_invoice_number else 1000

            except sqlite3.Error as e:
                self.show_custom_message("critical", "خطای پایگاه داده", f"{translate_sqlite_error(e)}")
                return 1000  # Default value on error

    def show_custom_message(self, typ, title, message, button1_text="متوجه شدم", button2_text=None):
        """Shows a message box with customized button text and returns the clicked button"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)

        # Set the icon based on the type
        if typ == "warning":
            msg_box.setIcon(QMessageBox.Warning)
        elif typ == "question":
            msg_box.setIcon(QMessageBox.Question)
        elif typ == "critical":
            msg_box.setIcon(QMessageBox.Critical)
        elif typ == "information":
            msg_box.setIcon(QMessageBox.Information)

        # Add buttons and store references
        ok_button = msg_box.addButton(button1_text, QMessageBox.AcceptRole)
        cancel_button = None
        if typ == "question" and button2_text:
            cancel_button = msg_box.addButton(button2_text, QMessageBox.RejectRole)

        # Show the dialog modally
        msg_box.exec()

        # Return the clicked button object
        clicked_button = msg_box.clickedButton()
        return clicked_button


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = InvoicePage(stacked_widget=None)

    sys.exit(app.exec())
