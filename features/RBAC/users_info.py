import sys
import sqlite3
from datetime import datetime, timedelta
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QTextEdit, QPushButton, QFrame,
                               QGroupBox, QMessageBox, QScrollArea, QSizePolicy)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap
from modules.RBAC.helper_functions import DatabaseWorker


class UserInformationWidget(QWidget):
    """UsersModel information display widget with scroll area"""

    def __init__(self, parent, username):
        super().__init__()
        self.username = username
        self.setup_ui()
        self.load_user_data()

    def setup_ui(self):
        """Setup the user information UI with scroll area"""
        # Main layout for the widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins from main widget

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)  # Remove frame for cleaner look

        # Create the content widget that will be scrolled
        content_widget = QWidget()
        content_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        # Setup the actual content layout
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Profile header
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Box)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-radius: 10px;
                padding: 20px;
            }
        """)

        header_layout = QHBoxLayout(header_frame)

        # Avatar placeholder
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(100, 100)
        self.avatar_label.setStyleSheet("""
            QLabel {
                background-color: #ddd;
                border-radius: 50px;
                border: 3px solid #007ACC;
            }
        """)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setText("تصویر")

        # UsersModel basic info
        info_layout = QVBoxLayout()
        self.name_label = QLabel("نام: در حال بارگذاری...")
        self.name_label.setFont(QFont("Arial", 16, QFont.Bold))

        self.role_label = QLabel("نقش: در حال بارگذاری...")
        self.role_label.setFont(QFont("Arial", 12))

        self.username_label = QLabel(f"نام کاربری: {self.username}")
        self.username_label.setFont(QFont("Arial", 12))

        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.role_label)
        info_layout.addWidget(self.username_label)
        info_layout.addStretch()

        header_layout.addWidget(self.avatar_label)
        header_layout.addLayout(info_layout)
        header_layout.addStretch()

        layout.addWidget(header_frame)

        # Detailed information
        details_group = QGroupBox("اطلاعات تفصیلی")
        details_group.setFont(QFont("Arial", 12, QFont.Bold))
        details_layout = QGridLayout(details_group)

        # Personal information fields
        fields = [
            ("تاریخ تولد:", "birth_date"),
            ("ایمیل:", "email"),
            ("تلفن:", "phone"),
            ("کد ملی:", "national_id"),
            ("آدرس:", "address")
        ]

        self.field_labels = {}

        for i, (label_text, field_name) in enumerate(fields):
            label = QLabel(label_text)
            label.setFont(QFont("Arial", 10, QFont.Bold))

            value_label = QLabel("در حال بارگذاری...")
            value_label.setStyleSheet("""
                QLabel {
                    background-color: white;
                    border: 1px solid #ddd;
                    padding: 8px;
                    border-radius: 4px;
                }
            """)

            self.field_labels[field_name] = value_label

            details_layout.addWidget(label, i, 0)
            details_layout.addWidget(value_label, i, 1)

        layout.addWidget(details_group)

        # Bio section
        bio_group = QGroupBox("بیوگرافی")
        bio_group.setFont(QFont("Arial", 12, QFont.Bold))
        bio_layout = QVBoxLayout(bio_group)

        self.bio_text = QTextEdit()
        self.bio_text.setReadOnly(True)
        self.bio_text.setMaximumHeight(100)
        self.bio_text.setPlaceholderText("بیوگرافی در حال بارگذاری...")

        bio_layout.addWidget(self.bio_text)
        layout.addWidget(bio_group)

        # Account information
        account_group = QGroupBox("اطلاعات حساب کاربری")
        account_group.setFont(QFont("Arial", 12, QFont.Bold))
        account_layout = QGridLayout(account_group)

        self.account_status_label = QLabel("وضعیت حساب: در حال بررسی...")
        self.start_date_label = QLabel("تاریخ شروع: در حال بارگذاری...")
        self.created_date_label = QLabel("تاریخ ایجاد: در حال بارگذاری...")

        account_layout.addWidget(QLabel("وضعیت:"), 0, 0)
        account_layout.addWidget(self.account_status_label, 0, 1)
        account_layout.addWidget(QLabel("تاریخ شروع کار:"), 1, 0)
        account_layout.addWidget(self.start_date_label, 1, 1)
        account_layout.addWidget(QLabel("تاریخ ایجاد حساب:"), 2, 0)
        account_layout.addWidget(self.created_date_label, 2, 1)

        layout.addWidget(account_group)

        # Refresh button
        refresh_btn = QPushButton("بروزرسانی اطلاعات")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        refresh_btn.clicked.connect(self.load_user_data)

        layout.addWidget(refresh_btn)
        layout.addStretch()

        # Set the content widget to the scroll area
        scroll_area.setWidget(content_widget)

        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)

    def load_user_data(self):
        """Load user data from database"""
        self.worker = DatabaseWorker(self.username, "profile")
        self.worker.data_loaded.connect(self.update_user_info)
        self.worker.start()

    def update_user_info(self, data):
        """Update UI with loaded user data"""
        if not data:
            QMessageBox.warning(self, "خطا", "خطا در بارگذاری اطلاعات کاربر")
            return

        profile = data.get('profile')
        user_info = data.get('user_info')

        if profile:
            # Update profile information
            self.name_label.setText(f"نام: {profile[0] or 'نامشخص'}")
            self.role_label.setText(f"نقش: {profile[1] or 'نامشخص'}")

            # Update detailed fields
            field_values = {
                'birth_date': profile[2] or 'ثبت نشده',
                'email': profile[3] or 'ثبت نشده',
                'phone': profile[4] or 'ثبت نشده',
                'national_id': profile[5] or 'ثبت نشده',
                'address': profile[6] or 'ثبت نشده'
            }

            for field_name, value in field_values.items():
                if field_name in self.field_labels:
                    self.field_labels[field_name].setText(str(value))

            # Update bio
            bio = profile[7] or "بیوگرافی ثبت نشده است."
            self.bio_text.setPlainText(bio)

            # Handle avatar
            avatar_path = profile[8]
            if avatar_path:
                # Load avatar image if exists
                pixmap = QPixmap(avatar_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.avatar_label.setPixmap(scaled_pixmap)
                    self.avatar_label.setText("")

        if user_info:
            # Update account information
            role_map = {
                'admin': 'مدیر',
                'translator': 'مترجم',
                'clerk': 'منشی',
                'accountant': 'حسابدار'
            }

            account_role = role_map.get(user_info[0], user_info[0])
            is_active = user_info[1]
            status_text = "فعال" if is_active else "غیرفعال"
            status_color = "green" if is_active else "red"

            self.account_status_label.setText(f"وضعیتحساب: {status_text}")
            self.account_status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")

            start_date = user_info[2] or "ثبت نشده"
            self.start_date_label.setText(f"تاریخ شروع کار: {start_date}")

            created_date = user_info[3] or "ثبت نشده"
            self.created_date_label.setText(f"تاریخ ایجاد حساب: {created_date}")
