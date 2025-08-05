import sqlite3

from modules.helper_functions import return_resource
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow, QTableWidget, QTableWidgetItem, QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
    QLineEdit, QDialog, QLabel, QMenu, QMessageBox, QHeaderView
)


customers_database = return_resource("databases", "customers.db")


class AddCustomerDialog(QDialog):
    def __init__(self, parent=None):
        """
        Dialog to add a new customer.
        """
        super().__init__(parent)
        self.setWindowTitle("افزودن مشتری")
        self.setGeometry(300, 300, 400, 300)

        # Layout
        layout = QVBoxLayout(self)

        # Labels and LineEdits
        self.fields = {}
        labels = ["کد ملی", "نام و نام خانوادگی", "شماره تماس",  "ایمیل", "آدرس"]
        for label_text in labels:
            label = QLabel(label_text)
            line_edit = QLineEdit()
            layout.addWidget(label)
            layout.addWidget(line_edit)
            self.fields[label_text] = line_edit

        # Save Button
        save_button = QPushButton("ذخیره")
        save_button.clicked.connect(self.save_customer)
        layout.addWidget(save_button)

    def save_customer(self):
        """Save the new customer to the database."""
        national_id = self.fields["کد ملی"].text().strip()
        name = self.fields["نام و نام خانوادگی"].text().strip()
        phone = self.fields["شماره تماس"].text().strip()
        email = self.fields["ایمیل"].text().strip()
        address = self.fields["آدرس"].text().strip()

        # Input Validation
        if not national_id or not name or not phone or not address:
            QMessageBox.warning(self, "خطا", "لطفاً تمام فیلدهای اجباری را پر کنید.")
            return

        if not (phone.isdigit() and 10 <= len(phone) <= 11):
            QMessageBox.warning(self, "خطا", "شماره تماس باید بین ۱۰ تا ۱۱ رقم باشد.")
            return

        if not (national_id.isdigit() and len(national_id) == 10):
            QMessageBox.warning(self, "خطا", "کد ملی باید دقیقاً ۱۰ رقم باشد.")
            return

        try:
            with sqlite3.connect(customers_database) as connection:
                cursor = connection.cursor()
                cursor.execute("""
                    INSERT INTO customers (national_id, name, phone, email, address)
                    VALUES (?, ?, ?, ?, ?)
                """, (national_id, name, phone, email, address))
                connection.commit()
                QMessageBox.information(self, "موفقیت", "مشتری جدید با موفقیت افزوده شد.")
                self.accept()  # Close dialog on success
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "خطا", "کد ملی یا شماره تماس وارد شده قبلاً ثبت شده است.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در افزودن مشتری: {e}")


class EditCustomerDialog(QDialog):
    def __init__(self, customer_data, parent=None):
        """
        Dialog to edit customer data.
        :param customer_data: Tuple of customer data (national_id, name, phone, address, invoice_no)
        """
        super().__init__(parent)
        self.setWindowTitle("ویرایش مشتری")
        self.setGeometry(300, 300, 400, 300)

        self.customer_data = customer_data

        # Layout
        layout = QVBoxLayout(self)

        # Labels and LineEdits
        self.fields = {}
        labels = ["کد ملی", "نام و نام خانوادگی", "شماره تماس",  "ایمیل", "آدرس"]
        for i, label_text in enumerate(labels):
            label = QLabel(label_text)
            line_edit = QLineEdit()
            line_edit.setText(str(customer_data[i]))
            layout.addWidget(label)
            layout.addWidget(line_edit)
            self.fields[label_text] = line_edit

        # Save Button
        save_button = QPushButton("ذخیره")
        save_button.clicked.connect(self.save_changes)
        layout.addWidget(save_button)

    def save_changes(self):
        """Save the changes to the database."""
        national_id = self.fields["کد ملی"].text()
        name = self.fields["نام و نام خانوادگی"].text()
        phone = self.fields["شماره تماس"].text()
        email = self.fields["ایمیل"].text().strip()
        address = self.fields["آدرس"].text()

        try:
            with sqlite3.connect(customers_database) as connection:
                cursor = connection.cursor()
                cursor.execute("""
                    UPDATE customers
                    SET name = ?, phone = ?,address = ?, email = ?
                    WHERE national_id = ?
                """, (name, phone, address, email, national_id))
                connection.commit()
            QMessageBox.information(self, "موفقیت", "اطلاعات مشتری با موفقیت ویرایش شد.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در ویرایش اطلاعات مشتری: {e}")
        finally:
            self.accept()  # Close dialog after saving


class CustomerTable(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CustomerModel Table")
        self.setGeometry(100, 100, 800, 600)

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        self.setLayoutDirection(Qt.RightToLeft)

        # Buttons
        self.buttons_layout = QHBoxLayout()
        self.delete_button = QPushButton("حذف مشتری")
        self.edit_button = QPushButton("ویرایش مشتری")
        self.add_button = QPushButton("اضافه کردن مشتری")
        self.delete_button.clicked.connect(self.delete_customer)
        self.edit_button.clicked.connect(self.edit_customer)
        self.add_button.clicked.connect(self.add_customer)
        self.buttons_layout.addWidget(self.delete_button)
        self.buttons_layout.addWidget(self.edit_button)
        self.buttons_layout.addWidget(self.add_button)

        # Search bar
        self.search_bar_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("جستجوی مشتری ...")
        self.search_bar.textChanged.connect(self.filter_data)
        self.search_bar_layout.addWidget(self.search_bar)
        self.layout.addLayout(self.search_bar_layout)
        self.layout.addLayout(self.buttons_layout)

        # Table widget
        self.table = QTableWidget()
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.layout.addWidget(self.table)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        # Load data into the table
        self.rows = []  # Initialize rows for filtering
        self.load_data()

    def load_data(self):
        """Load customer data from the database into the QTableWidget."""
        with sqlite3.connect(customers_database) as connection:
            cursor = connection.cursor()

        try:
            cursor.execute("SELECT * FROM customers")
            self.rows = cursor.fetchall()  # Store rows for filtering

            self.table.setRowCount(len(self.rows))
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(
                ["کد ملی", "نام و نام خانوادگی", "شماره تماس", "ایمیل", "آدرس"])

            for row_idx, row in enumerate(self.rows):
                for col_idx, value in enumerate(row):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای پایگاه داده", f"Database error: {e}")

    def filter_data(self):
        """Filter the table based on the search bar input."""
        filter_text = self.search_bar.text().lower()
        self.table.setRowCount(0)

        for row in self.rows:
            if any(filter_text in str(value).lower() for value in row):
                row_idx = self.table.rowCount()
                self.table.insertRow(row_idx)

                for col_idx, value in enumerate(row):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

    def show_context_menu(self, position):
        """Show a context menu when right-clicking on a table item."""
        menu = QMenu()

        delete_action = QAction("حذف مشتری", self)
        delete_action.triggered.connect(self.delete_customer)
        menu.addAction(delete_action)

        edit_action = QAction("ویرایش مشتری", self)
        edit_action.triggered.connect(self.edit_customer)
        menu.addAction(edit_action)

        menu.exec(self.table.viewport().mapToGlobal(position))

    def delete_customer(self):
        """Delete the selected customer from the database."""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            return

        national_id = self.table.item(selected_row, 0).text()

        reply = QMessageBox.question(
            self, "حذف مشتری", "آیا مطمئن هستید که می‌خواهید این مشتری را حذف کنید؟",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                with sqlite3.connect(customers_database) as connection:
                    cursor = connection.cursor()
                    cursor.execute("DELETE FROM customers WHERE national_id = ?", (national_id,))
                    connection.commit()
                    QMessageBox.information(self, "موفقیت", "مشتری با موفقیت حذف شد.")
                    self.load_data()  # Reload the table after deletion
            except sqlite3.Error as e:
                QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در حذف مشتری: {e}")

    def edit_customer(self):
        """Open a dialog to edit the selected customer."""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            return

        customer_data = [
            self.table.item(selected_row, col).text()
            for col in range(self.table.columnCount())
        ]
        dialog = EditCustomerDialog(customer_data, self)
        if dialog.exec():
            self.load_data()  # Reload the table after editing

    def add_customer(self):
        """Open the AddCustomerDialog to add a new customer."""
        dialog = AddCustomerDialog(self)
        if dialog.exec():  # If the dialog is accepted
            self.load_data()  # Reload data in the table after adding the customer
