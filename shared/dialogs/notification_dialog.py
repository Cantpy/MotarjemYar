"""
Notification dialog for sending SMS and Email notifications to customers.
"""
import sqlite3
import requests
import re
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QLabel,
    QLineEdit, QTextEdit, QPushButton, QMessageBox, QListWidget,
    QFileDialog, QListWidgetItem, QMenu
)
from PySide6.QtCore import Qt


class NotificationDialog(QDialog):
    """Dialog for sending SMS or Email notifications to customers."""

    def __init__(self, invoice_number, invoices_database, customers_database, parent=None):
        super().__init__(parent)
        self.invoice_number = invoice_number
        self.invoices_database = invoices_database
        self.customers_database = customers_database
        self.customer_data = self._get_customer_data()
        self.uploaded_files = []
        self._setup_ui()

    def _get_customer_data(self):
        """Get customer data from database based on invoice number."""
        try:
            with sqlite3.connect(self.invoices_database) as inv_conn:
                cursor = inv_conn.cursor()
                cursor.execute(
                    "SELECT name, phone FROM issued_invoices WHERE invoice_number = ?",
                    (self.invoice_number,)
                )
                result = cursor.fetchone()
                if not result:
                    return {"name": "", "phone": "", "email": ""}

                name, phone = result

            # Get email from customers database
            with sqlite3.connect(self.customers_database) as cust_conn:
                cursor = cust_conn.cursor()
                cursor.execute(
                    "SELECT email FROM customers WHERE name = ? AND phone = ?",
                    (name, phone)
                )
                email_result = cursor.fetchone()
                email = email_result[0] if email_result else ""

            return {"name": name, "phone": phone, "email": email}

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در خواندن اطلاعات مشتری: {e}")
            return {"name": "", "phone": "", "email": ""}

    def _setup_ui(self):
        """Setup the dialog UI with tabs."""
        self.setWindowTitle("ارسال اطلاعیه")
        self.setModal(True)
        self.resize(600, 500)

        layout = QVBoxLayout(self)

        # Create tab widget
        self.tab_widget = QTabWidget()

        # SMS Tab
        sms_tab = self._create_sms_tab()
        self.tab_widget.addTab(sms_tab, "پیامک")

        # Email Tab
        email_tab = self._create_email_tab()
        self.tab_widget.addTab(email_tab, "ایمیل")

        layout.addWidget(self.tab_widget)

        # Buttons
        button_layout = QHBoxLayout()

        send_btn = QPushButton("ارسال")
        send_btn.clicked.connect(self._send_notification)

        cancel_btn = QPushButton("لغو")
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(send_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _create_sms_tab(self):
        """Create SMS tab content."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Name field
        layout.addWidget(QLabel("نام مشتری:"))
        self.sms_name_edit = QLineEdit()
        self.sms_name_edit.setText(self.customer_data["name"])
        layout.addWidget(self.sms_name_edit)

        # Phone field
        layout.addWidget(QLabel("شماره تماس:"))
        self.sms_phone_edit = QLineEdit()
        self.sms_phone_edit.setText(self.customer_data["phone"])
        layout.addWidget(self.sms_phone_edit)

        # Message field with rich text editor
        layout.addWidget(QLabel("متن پیام:"))
        self.sms_text_edit = QTextEdit()
        self.sms_text_edit.setPlainText("متن پیام خود را اینجا وارد کنید...")
        layout.addWidget(self.sms_text_edit)

        return widget

    def _create_email_tab(self):
        """Create Email tab content."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Name field
        layout.addWidget(QLabel("نام مشتری:"))
        self.email_name_edit = QLineEdit()
        self.email_name_edit.setText(self.customer_data["name"])
        layout.addWidget(self.email_name_edit)

        # Email field
        layout.addWidget(QLabel("ایمیل (اجباری):"))
        self.email_address_edit = QLineEdit()
        self.email_address_edit.setText(self.customer_data["email"])
        layout.addWidget(self.email_address_edit)

        # Message field with rich text editor
        layout.addWidget(QLabel("متن ایمیل:"))
        self.email_text_edit = QTextEdit()
        self.email_text_edit.setPlainText("متن ایمیل خود را اینجا وارد کنید...")
        layout.addWidget(self.email_text_edit)

        # File upload section
        layout.addWidget(QLabel("فایل‌های پیوست:"))

        file_layout = QHBoxLayout()
        upload_btn = QPushButton("انتخاب فایل")
        upload_btn.clicked.connect(self._upload_files)
        file_layout.addWidget(upload_btn)

        remove_btn = QPushButton("حذف فایل انتخابی")
        remove_btn.clicked.connect(self._remove_selected_file)
        file_layout.addWidget(remove_btn)

        clear_all_btn = QPushButton("حذف همه فایل‌ها")
        clear_all_btn.clicked.connect(self._clear_all_files)
        file_layout.addWidget(clear_all_btn)

        self.file_count_label = QLabel("هیچ فایلی انتخاب نشده")
        file_layout.addWidget(self.file_count_label)

        layout.addLayout(file_layout)

        # File list with context menu
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(100)
        self.file_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self._show_file_context_menu)
        layout.addWidget(self.file_list)

        return widget

    def _upload_files(self):
        """Handle file upload for email."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "انتخاب فایل‌ها",
            "",
            "All Files (*)"
        )

        if files:
            # Check for duplicates before adding
            new_files = [f for f in files if f not in self.uploaded_files]
            if new_files:
                self.uploaded_files.extend(new_files)
                self._update_file_list()

            if len(new_files) < len(files):
                QMessageBox.information(
                    self,
                    "فایل‌های تکراری",
                    "برخی فایل‌ها قبلاً انتخاب شده‌اند و نادیده گرفته شدند."
                )

    def _remove_selected_file(self):
        """Remove selected file from the list."""
        current_row = self.file_list.currentRow()
        if current_row >= 0:
            # Remove from uploaded_files list
            removed_file = self.uploaded_files.pop(current_row)
            self._update_file_list()
            QMessageBox.information(
                self,
                "حذف فایل",
                f"فایل '{removed_file.split('/')[-1]}' حذف شد."
            )
        else:
            QMessageBox.warning(self, "خطا", "لطفاً فایلی را برای حذف انتخاب کنید.")

    def _clear_all_files(self):
        """Clear all uploaded files."""
        if self.uploaded_files:
            reply = QMessageBox.question(
                self,
                "حذف همه فایل‌ها",
                "آیا مطمئن هستید که می‌خواهید همه فایل‌ها را حذف کنید؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.uploaded_files.clear()
                self._update_file_list()
                QMessageBox.information(self, "حذف فایل‌ها", "همه فایل‌ها حذف شدند.")

    def _show_file_context_menu(self, position):
        """Show context menu for file list."""
        if self.file_list.itemAt(position) is not None:
            context_menu = QMenu(self)

            remove_action = context_menu.addAction("حذف این فایل")
            remove_action.triggered.connect(self._remove_selected_file)

            context_menu.addSeparator()

            clear_all_action = context_menu.addAction("حذف همه فایل‌ها")
            clear_all_action.triggered.connect(self._clear_all_files)

            context_menu.exec(self.file_list.mapToGlobal(position))

    def _update_file_list(self):
        """Update the file list display."""
        self.file_list.clear()

        for file_path in self.uploaded_files:
            file_name = file_path.split('/')[-1]  # Get filename only
            item = QListWidgetItem(file_name)
            item.setToolTip(file_path)  # Show full path in tooltip
            self.file_list.addItem(item)

        count = len(self.uploaded_files)
        if count == 0:
            self.file_count_label.setText("هیچ فایلی انتخاب نشده")
        else:
            self.file_count_label.setText(f"{count} فایل انتخاب شده")

    def _validate_email(self, email):
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _update_customer_email(self, email):
        """Update customer email in database."""
        try:
            with sqlite3.connect(self.customers_database) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE customers SET email = ? WHERE name = ? AND phone = ?",
                    (email, self.customer_data["name"], self.customer_data["phone"])
                )
                if cursor.rowcount > 0:
                    return True
                else:
                    # If no rows were updated, try to insert new customer record
                    cursor.execute(
                        "INSERT OR IGNORE INTO customers (name, phone, email) VALUES (?, ?, ?)",
                        (self.customer_data["name"], self.customer_data["phone"], email)
                    )
                    return cursor.rowcount > 0
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در به‌روزرسانی ایمیل: {e}")
            return False

    def _send_notification(self):
        """Send notification based on active tab."""
        current_tab = self.tab_widget.currentIndex()

        if current_tab == 0:  # SMS tab
            self._send_sms()
        else:  # Email tab
            self._send_email()

    def _send_sms(self):
        """Send SMS notification."""
        # Get values or use placeholders
        name = self.sms_name_edit.text() or self.customer_data["name"]
        phone = self.sms_phone_edit.text() or self.customer_data["phone"]
        message = self.sms_text_edit.toPlainText()

        if not phone:
            QMessageBox.warning(self, "خطا", "شماره تماس وارد نشده است")
            return

        if not message:
            QMessageBox.warning(self, "خطا", "متن پیام وارد نشده است")
            return

        try:
            self._execute_sms_send(phone, message)
            QMessageBox.information(self, "موفقیت", "پیامک با موفقیت ارسال شد")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "خطا در ارسال", f"خطا در ارسال پیامک: {str(e)}")

    def _execute_sms_send(self, recipient, text):
        """Execute SMS sending using the provided API."""
        url = 'https://console.melipayamak.com/api/send/simple/02518acf41404001be90c2baafb85767'

        data = {
            'from': '50002710094507',
            'to': recipient,
            'text': text
        }

        response = requests.post(url, json=data)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"SMS sending failed: {response.status_code} - {response.text}")

    def _send_email(self):
        """Send email notification with validation."""
        name = self.email_name_edit.text() or self.customer_data["name"]
        email = self.email_address_edit.text().strip()
        message = self.email_text_edit.toPlainText()

        # Validate email field (mandatory)
        if not email:
            QMessageBox.warning(self, "خطا", "وارد کردن آدرس ایمیل اجباری است")
            self.email_address_edit.setFocus()
            return

        # Validate email format
        if not self._validate_email(email):
            QMessageBox.warning(self, "خطای فرمت", "فرمت آدرس ایمیل صحیح نیست")
            self.email_address_edit.setFocus()
            return

        if not message:
            QMessageBox.warning(self, "خطا", "متن ایمیل وارد نشده است")
            return

        # Update customer email in database if it's different
        if email != self.customer_data["email"]:
            if self._update_customer_email(email):
                QMessageBox.information(
                    self,
                    "به‌روزرسانی",
                    "آدرس ایمیل مشتری در پایگاه داده به‌روزرسانی شد."
                )

        # Placeholder for email functionality
        QMessageBox.information(
            self,
            "در حال توسعه",
            f"ارسال ایمیل به {email} با {len(self.uploaded_files)} فایل پیوست\n"
            f"متن ایمیل: {message[:50]}{'...' if len(message) > 50 else ''}\n"
            "(این قابلیت در حال توسعه است)"
        )
        self.accept()
