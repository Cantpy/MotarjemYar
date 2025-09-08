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
from PySide6.QtCore import Qt, Signal
from shared.dtos.notification_dialog_dtos import SmsRequestDTO, EmailRequestDTO, NotificationDataDTO


class NotificationDialog(QDialog):
    """Dialog for sending SMS or Email notifications to customers."""
    send_sms_requested = Signal(SmsRequestDTO)
    send_email_requested = Signal(EmailRequestDTO)

    def __init__(self, data: NotificationDataDTO, parent=None):
        super().__init__(parent)
        self.customer_data = data  # Store the DTO
        self.uploaded_files = []
        self._setup_ui()

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
        send_btn.clicked.connect(self._on_send_clicked)

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
        self.sms_name_edit.setText(self.customer_data.customer_name)
        layout.addWidget(self.sms_name_edit)

        # Phone field
        layout.addWidget(QLabel("شماره تماس:"))
        self.sms_phone_edit = QLineEdit()
        self.sms_phone_edit.setText(self.customer_data.customer_phone)
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
        self.email_name_edit.setText(self.customer_data.customer_name)
        layout.addWidget(self.email_name_edit)

        # Email field
        layout.addWidget(QLabel("ایمیل (اجباری):"))
        self.email_address_edit = QLineEdit()
        self.email_address_edit.setText(self.customer_data.customer_email)
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

    def _on_send_clicked(self):
        """
        Gathers data from the form fields and emits the appropriate signal.
        This is the dialog's only "action" logic.
        """
        current_tab = self.tab_widget.currentIndex()

        if current_tab == 0:  # SMS tab
            phone = self.sms_phone_edit.text()
            message = self.sms_text_edit.toPlainText()
            if not phone or not message:
                QMessageBox.warning(self, "خطا", "شماره تماس و متن پیام الزامی است.")
                return
            # Emit a signal with a DTO
            request_dto = SmsRequestDTO(recipient_phone=phone, message=message)
            self.send_sms_requested.emit(request_dto)

        else:  # Email tab
            name = self.email_name_edit.text()
            email = self.email_address_edit.text()
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

            # Emit a signal with a DTO
            request_dto = EmailRequestDTO(
                recipient_name=name,
                recipient_email=email,
                message=message,
                attachments=self.uploaded_files
            )
            self.send_email_requested.emit(request_dto)

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
