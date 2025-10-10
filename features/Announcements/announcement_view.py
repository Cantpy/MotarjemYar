"""
PySide6 _view for the Notification History widget.
"""
import os
import sys
from datetime import datetime
from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QPushButton, QLineEdit,
    QComboBox, QDateEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QFrame, QSplitter, QTextEdit, QFileDialog, QMessageBox,
    QProgressBar, QStatusBar, QGroupBox, QGridLayout, QSpacerItem,
    QSizePolicy, QMenu, QDialog, QDialogButtonBox, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QDate, QTimer, Signal
from PySide6.QtGui import QFont, QIcon, QPixmap, QAction
from features.Announcements.announcement_models import NotificationStatus, SMSNotification, EmailNotification
from features.Announcements.announcemnet_controller import NotificationController


class NotificationHistoryWidget(QWidget):
    """Main widget for displaying notification history."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = NotificationController()
        self.setup_ui()
        self.connect_signals()
        self.get_notification_history_stylesheet()

    def setup_ui(self):
        """Setup the user interface."""
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header with title and new notification button
        header_layout = self.create_header()
        layout.addLayout(header_layout)

        # Main content with tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)

        # SMS Tab
        self.sms_tab = self.create_sms_tab()
        self.tab_widget.addTab(self.sms_tab, "📱 پیامک‌ها")

        # Email Tab
        self.email_tab = self.create_email_tab()
        self.tab_widget.addTab(self.email_tab, "📧 ایمیل‌ها")

        layout.addWidget(self.tab_widget)

        # Status bar
        self.status_bar = QStatusBar()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        layout.addWidget(self.status_bar)

    def create_header(self) -> QHBoxLayout:
        """Create header layout."""
        layout = QHBoxLayout()

        # Title
        title_label = QLabel("سابقه اطلاعیه‌ها")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        layout.addStretch()

        # New notification button
        self.new_notification_btn = QPushButton("ارسال اطلاعیه جدید")
        self.new_notification_btn.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005999;
            }
        """)
        self.new_notification_btn.clicked.connect(self.show_new_notification_dialog)
        layout.addWidget(self.new_notification_btn)

        # Refresh button
        self.refresh_btn = QPushButton("بروزرسانی")
        self.refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(self.refresh_btn)

        return layout

    def create_sms_tab(self) -> QWidget:
        """Create SMS tab content."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filters section
        filters_group = self.create_sms_filters()
        layout.addWidget(filters_group)

        # SMS table
        self.sms_table = self.create_sms_table()
        layout.addWidget(self.sms_table)

        # Pagination
        pagination_layout = self.create_sms_pagination()
        layout.addLayout(pagination_layout)

        return widget

    def create_email_tab(self) -> QWidget:
        """Create Email tab content."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filters section
        filters_group = self.create_email_filters()
        layout.addWidget(filters_group)

        # Email table
        self.email_table = self.create_email_table()
        layout.addWidget(self.email_table)

        # Pagination
        pagination_layout = self.create_email_pagination()
        layout.addLayout(pagination_layout)

        return widget

    def create_sms_filters(self) -> QGroupBox:
        """Create SMS filters section."""
        group = QGroupBox("فیلترها")
        layout = QGridLayout(group)

        # Search box
        layout.addWidget(QLabel("جستجو:"), 0, 0)
        self.sms_search_edit = QLineEdit()
        self.sms_search_edit.setPlaceholderText("جستجو در نام، شماره یا متن پیام...")
        self.sms_search_edit.textChanged.connect(self.apply_sms_filters)
        layout.addWidget(self.sms_search_edit, 0, 1, 1, 2)

        # Status filter
        layout.addWidget(QLabel("وضعیت:"), 1, 0)
        self.sms_status_combo = QComboBox()
        self.sms_status_combo.addItems(["همه", "در انتظار", "ارسال شده", "ناموفق", "تحویل داده شده"])
        self.sms_status_combo.currentTextChanged.connect(self.apply_sms_filters)
        layout.addWidget(self.sms_status_combo, 1, 1)

        # Date filters
        layout.addWidget(QLabel("از تاریخ:"), 1, 2)
        self.sms_date_from = QDateEdit()
        self.sms_date_from.setCalendarPopup(True)
        self.sms_date_from.setDate(QDate.currentDate().addDays(-30))
        self.sms_date_from.dateChanged.connect(self.apply_sms_filters)
        layout.addWidget(self.sms_date_from, 1, 3)

        layout.addWidget(QLabel("تا تاریخ:"), 1, 4)
        self.sms_date_to = QDateEdit()
        self.sms_date_to.setCalendarPopup(True)
        self.sms_date_to.setDate(QDate.currentDate())
        self.sms_date_to.dateChanged.connect(self.apply_sms_filters)
        layout.addWidget(self.sms_date_to, 1, 5)

        # Quick date filters
        quick_dates_layout = QHBoxLayout()
        quick_dates = [
            ("امروز", "today"),
            ("دیروز", "yesterday"),
            ("این هفته", "this_week"),
            ("هفته گذشته", "last_week"),
            ("این ماه", "this_month"),
            ("ماه گذشته", "last_month")
        ]

        for text, filter_type in quick_dates:
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, ft=filter_type: self.apply_quick_date_filter(ft, "sms"))
            quick_dates_layout.addWidget(btn)

        layout.addLayout(quick_dates_layout, 2, 0, 1, 6)

        # Action buttons
        actions_layout = QHBoxLayout()

        clear_filters_btn = QPushButton("پاک کردن فیلترها")
        clear_filters_btn.clicked.connect(self.clear_sms_filters)
        actions_layout.addWidget(clear_filters_btn)

        export_btn = QPushButton("خروجی CSV")
        export_btn.clicked.connect(self.export_sms_data)
        actions_layout.addWidget(export_btn)

        actions_layout.addStretch()
        layout.addLayout(actions_layout, 3, 0, 1, 6)

        return group

    def create_email_filters(self) -> QGroupBox:
        """Create Email filters section."""
        group = QGroupBox("فیلترها")
        layout = QGridLayout(group)

        # Search box
        layout.addWidget(QLabel("جستجو:"), 0, 0)
        self.email_search_edit = QLineEdit()
        self.email_search_edit.setPlaceholderText("جستجو در نام، ایمیل، موضوع یا متن...")
        self.email_search_edit.textChanged.connect(self.apply_email_filters)
        layout.addWidget(self.email_search_edit, 0, 1, 1, 2)

        # Status filter
        layout.addWidget(QLabel("وضعیت:"), 1, 0)
        self.email_status_combo = QComboBox()
        self.email_status_combo.addItems(["همه", "در انتظار", "ارسال شده", "ناموفق", "تحویل داده شده"])
        self.email_status_combo.currentTextChanged.connect(self.apply_email_filters)
        layout.addWidget(self.email_status_combo, 1, 1)

        # Date filters
        layout.addWidget(QLabel("از تاریخ:"), 1, 2)
        self.email_date_from = QDateEdit()
        self.email_date_from.setCalendarPopup(True)
        self.email_date_from.setDate(QDate.currentDate().addDays(-30))
        self.email_date_from.dateChanged.connect(self.apply_email_filters)
        layout.addWidget(self.email_date_from, 1, 3)

        layout.addWidget(QLabel("تا تاریخ:"), 1, 4)
        self.email_date_to = QDateEdit()
        self.email_date_to.setCalendarPopup(True)
        self.email_date_to.setDate(QDate.currentDate())
        self.email_date_to.dateChanged.connect(self.apply_email_filters)
        layout.addWidget(self.email_date_to, 1, 5)

        # Quick date filters
        quick_dates_layout = QHBoxLayout()
        quick_dates = [
            ("امروز", "today"),
            ("دیروز", "yesterday"),
            ("این هفته", "this_week"),
            ("هفته گذشته", "last_week"),
            ("این ماه", "this_month"),
            ("ماه گذشته", "last_month")
        ]

        for text, filter_type in quick_dates:
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, ft=filter_type: self.apply_quick_date_filter(ft, "email"))
            quick_dates_layout.addWidget(btn)

        layout.addLayout(quick_dates_layout, 2, 0, 1, 6)

        # Action buttons
        actions_layout = QHBoxLayout()

        clear_filters_btn = QPushButton("پاک کردن فیلترها")
        clear_filters_btn.clicked.connect(self.clear_email_filters)
        actions_layout.addWidget(clear_filters_btn)

        export_btn = QPushButton("خروجی CSV")
        export_btn.clicked.connect(self.export_email_data)
        actions_layout.addWidget(export_btn)

        actions_layout.addStretch()
        layout.addLayout(actions_layout, 3, 0, 1, 6)

        return group

    def create_sms_table(self) -> QTableWidget:
        """Create SMS table."""
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "نام گیرنده", "شماره تماس", "متن پیام", "وضعیت", "تاریخ ارسال", "تاریخ ایجاد"
        ])

        # Set column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(self.show_sms_context_menu)
        table.itemDoubleClicked.connect(self.show_sms_details)

        return table

    def create_email_table(self) -> QTableWidget:
        """Create Email table."""
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "نام گیرنده", "آدرس ایمیل", "موضوع", "وضعیت", "پیوست", "تاریخ ارسال", "تاریخ ایجاد"
        ])

        # Set column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(self.show_email_context_menu)
        table.itemDoubleClicked.connect(self.show_email_details)

        return table

    def create_sms_pagination(self) -> QHBoxLayout:
        """Create SMS pagination controls."""
        layout = QHBoxLayout()

        self.sms_prev_btn = QPushButton("قبلی")
        self.sms_prev_btn.clicked.connect(self.sms_prev_page)
        layout.addWidget(self.sms_prev_btn)

        self.sms_page_label = QLabel("صفحه 1 از 1")
        layout.addWidget(self.sms_page_label)

        self.sms_next_btn = QPushButton("بعدی")
        self.sms_next_btn.clicked.connect(self.sms_next_page)
        layout.addWidget(self.sms_next_btn)

        layout.addStretch()

        self.sms_count_label = QLabel("0 پیامک")
        layout.addWidget(self.sms_count_label)

        return layout

    def create_email_pagination(self) -> QHBoxLayout:
        """Create Email pagination controls."""
        layout = QHBoxLayout()

        self.email_prev_btn = QPushButton("قبلی")
        self.email_prev_btn.clicked.connect(self.email_prev_page)
        layout.addWidget(self.email_prev_btn)

        self.email_page_label = QLabel("صفحه 1 از 1")
        layout.addWidget(self.email_page_label)

        self.email_next_btn = QPushButton("بعدی")
        self.email_next_btn.clicked.connect(self.email_next_page)
        layout.addWidget(self.email_next_btn)

        layout.addStretch()

        self.email_count_label = QLabel("0 ایمیل")
        layout.addWidget(self.email_count_label)

        return layout

    def connect_signals(self):
        """Connect controller signals to _view slots."""
        self.controller.sms_data_changed.connect(self.update_sms_table)
        self.controller.email_data_changed.connect(self.update_email_table)
        self.controller.loading_changed.connect(self.set_loading)
        self.controller.error_occurred.connect(self.show_error)
        self.controller.status_updated.connect(self.update_status)

    def setup_styling(self):
        """Setup widget styling."""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QTableWidget {
                gridline-color: #f0f0f0;
                background-color: white;
                alternate-background-color: #f9f9f9;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: #f8f9fa;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)

    # Data update methods
    def update_sms_table(self):
        """Update SMS table with current data."""
        sms_list = self.controller.current_sms_list
        self.sms_table.setRowCount(len(sms_list))

        for row, sms in enumerate(sms_list):
            # Name
            self.sms_table.setItem(row, 0, QTableWidgetItem(sms.recipient_name))

            # Phone
            self.sms_table.setItem(row, 1, QTableWidgetItem(sms.recipient_phone))

            # MessageModel (truncated)
            message_preview = sms.message[:50] + "..." if len(sms.message) > 50 else sms.message
            self.sms_table.setItem(row, 2, QTableWidgetItem(message_preview))

            # Status
            status_item = QTableWidgetItem(self.controller.get_status_display(sms.status))
            status_item.setBackground(self.get_status_color(sms.status))
            self.sms_table.setItem(row, 3, status_item)

            # Sent date
            sent_date = sms.sent_at.strftime('%Y-%m-%d %H:%M') if sms.sent_at else ""
            self.sms_table.setItem(row, 4, QTableWidgetItem(sent_date))

            # Created date
            created_date = sms.created_at.strftime('%Y-%m-%d %H:%M')
            self.sms_table.setItem(row, 5, QTableWidgetItem(created_date))

            # Store SMS ID in first column for reference
            self.sms_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, sms.id)

        self.update_sms_pagination()

    def update_email_table(self):
        """Update Email table with current data."""
        email_list = self.controller.current_email_list
        self.email_table.setRowCount(len(email_list))

        for row, email in enumerate(email_list):
            # Name
            self.email_table.setItem(row, 0, QTableWidgetItem(email.recipient_name))

            # Email
            self.email_table.setItem(row, 1, QTableWidgetItem(email.recipient_email))

            # Subject
            self.email_table.setItem(row, 2, QTableWidgetItem(email.subject))

            # Status
            status_item = QTableWidgetItem(self.controller.get_status_display(email.status))
            status_item.setBackground(self.get_status_color(email.status))
            self.email_table.setItem(row, 3, status_item)

            # Attachments
            attachment_count = len(email.attachments)
            attachment_text = f"{attachment_count} فایل" if attachment_count > 0 else "بدون پیوست"
            self.email_table.setItem(row, 4, QTableWidgetItem(attachment_text))

            # Sent date
            sent_date = email.sent_at.strftime('%Y-%m-%d %H:%M') if email.sent_at else ""
            self.email_table.setItem(row, 5, QTableWidgetItem(sent_date))

            # Created date
            created_date = email.created_at.strftime('%Y-%m-%d %H:%M')
            self.email_table.setItem(row, 6, QTableWidgetItem(created_date))

            # Store Email ID in first column for reference
            self.email_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, email.id)

        self.update_email_pagination()

    def get_status_color(self, status: NotificationStatus):
        """Get color for status display."""
        from PySide6.QtGui import QColor
        colors = {
            NotificationStatus.PENDING: QColor(255, 193, 7),  # Yellow
            NotificationStatus.SENT: QColor(40, 167, 69),  # Green
            NotificationStatus.FAILED: QColor(220, 53, 69),  # Red
            NotificationStatus.DELIVERED: QColor(23, 162, 184)  # Blue
        }
        return colors.get(status, QColor(108, 117, 125))  # Gray default

    def update_sms_pagination(self):
        """Update SMS pagination controls."""
        current_page, max_pages, total_count = self.controller.get_current_sms_page_info()

        self.sms_page_label.setText(f"صفحه {current_page} از {max_pages}")
        self.sms_count_label.setText(f"{total_count} پیامک")

        self.sms_prev_btn.setEnabled(current_page > 1)
        self.sms_next_btn.setEnabled(current_page < max_pages)

    def update_email_pagination(self):
        """Update Email pagination controls."""
        current_page, max_pages, total_count = self.controller.get_current_email_page_info()

        self.email_page_label.setText(f"صفحه {current_page} از {max_pages}")
        self.email_count_label.setText(f"{total_count} ایمیل")

        self.email_prev_btn.setEnabled(current_page > 1)
        self.email_next_btn.setEnabled(current_page < max_pages)

    # Event handlers
    def apply_sms_filters(self):
        """Apply SMS filters."""
        search_text = self.sms_search_edit.text()
        status = self.get_status_from_combo(self.sms_status_combo.currentText())
        date_from = self.sms_date_from.date().toPython()
        date_to = self.sms_date_to.date().toPython()

        # Convert dates to datetime
        date_from = datetime.combine(date_from, datetime.min.time())
        date_to = datetime.combine(date_to, datetime.max.time())

        self.controller.filter_sms(search_text, status, date_from, date_to)

    def apply_email_filters(self):
        """Apply Email filters."""
        search_text = self.email_search_edit.text()
        status = self.get_status_from_combo(self.email_status_combo.currentText())
        date_from = self.email_date_from.date().toPython()
        date_to = self.email_date_to.date().toPython()

        # Convert dates to datetime
        date_from = datetime.combine(date_from, datetime.min.time())
        date_to = datetime.combine(date_to, datetime.max.time())

        self.controller.filter_email(search_text, status, date_from, date_to)

    def get_status_from_combo(self, text: str) -> Optional[NotificationStatus]:
        """Convert combo box text to NotificationStatus."""
        status_map = {
            "در انتظار": NotificationStatus.PENDING,
            "ارسال شده": NotificationStatus.SENT,
            "ناموفق": NotificationStatus.FAILED,
            "تحویل داده شده": NotificationStatus.DELIVERED
        }
        return status_map.get(text)

    def apply_quick_date_filter(self, filter_type: str, notification_type: str):
        """Apply quick date filter."""
        self.controller.apply_quick_date_filter(filter_type, notification_type)

    def clear_sms_filters(self):
        """Clear SMS filters."""
        self.sms_search_edit.clear()
        self.sms_status_combo.setCurrentIndex(0)
        self.sms_date_from.setDate(QDate.currentDate().addDays(-30))
        self.sms_date_to.setDate(QDate.currentDate())
        self.controller.clear_sms_filters()

    def clear_email_filters(self):
        """Clear Email filters."""
        self.email_search_edit.clear()
        self.email_status_combo.setCurrentIndex(0)
        self.email_date_from.setDate(QDate.currentDate().addDays(-30))
        self.email_date_to.setDate(QDate.currentDate())
        self.controller.clear_email_filters()

    # Pagination methods
    def sms_prev_page(self):
        """Go to previous SMS page."""
        current_page, _, _ = self.controller.get_current_sms_page_info()
        if current_page > 1:
            self.controller.go_to_sms_page(current_page - 1)

    def sms_next_page(self):
        """Go to next SMS page."""
        current_page, max_pages, _ = self.controller.get_current_sms_page_info()
        if current_page < max_pages:
            self.controller.go_to_sms_page(current_page + 1)

    def email_prev_page(self):
        """Go to previous Email page."""
        current_page, _, _ = self.controller.get_current_email_page_info()
        if current_page > 1:
            self.controller.go_to_email_page(current_page - 1)

    def email_next_page(self):
        """Go to next Email page."""
        current_page, max_pages, _ = self.controller.get_current_email_page_info()
        if current_page < max_pages:
            self.controller.go_to_email_page(current_page + 1)

    # Context menu methods
    def show_sms_context_menu(self, position):
        """Show SMS services menu."""
        if self.sms_table.itemAt(position) is not None:
            menu = QMenu(self)

            view_action = menu.addAction("مشاهده جزئیات")
            view_action.triggered.connect(self.show_sms_details)

            menu.addSeparator()

            resend_action = menu.addAction("ارسال مجدد")
            resend_action.triggered.connect(self.resend_sms)

            menu.exec(self.sms_table.mapToGlobal(position))

    def show_email_context_menu(self, position):
        """Show Email services menu."""
        if self.email_table.itemAt(position) is not None:
            menu = QMenu(self)

            view_action = menu.addAction("مشاهده جزئیات")
            view_action.triggered.connect(self.show_email_details)

            menu.addSeparator()

            resend_action = menu.addAction("ارسال مجدد")
            resend_action.triggered.connect(self.resend_email)

            menu.exec(self.email_table.mapToGlobal(position))

    def show_sms_details(self, item=None):
        """Show SMS details dialog."""
        current_row = self.sms_table.currentRow()
        if current_row >= 0:
            sms_id = self.sms_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            sms = self.controller.get_sms_by_id(sms_id)
            if sms:
                dialog = SMSDetailsDialog(sms, self)
                dialog.exec()

    def show_email_details(self, item=None):
        """Show Email details dialog."""
        current_row = self.email_table.currentRow()
        if current_row >= 0:
            email_id = self.email_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            email = self.controller.get_email_by_id(email_id)
            if email:
                dialog = EmailDetailsDialog(email, self)
                dialog.exec()

    def resend_sms(self):
        """Resend selected SMS."""
        current_row = self.sms_table.currentRow()
        if current_row >= 0:
            sms_id = self.sms_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            sms = self.controller.get_sms_by_id(sms_id)
            if sms:
                reply = QMessageBox.question(
                    self, "ارسال مجدد پیامک",
                    f"آیا مطمئن هستید که می‌خواهید پیامک به {sms.recipient_name} ارسال مجدد شود؟",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.controller.send_sms(sms.recipient_name, sms.recipient_phone, sms.message)

    def resend_email(self):
        """Resend selected Email."""
        current_row = self.email_table.currentRow()
        if current_row >= 0:
            email_id = self.email_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            email = self.controller.get_email_by_id(email_id)
            if email:
                reply = QMessageBox.question(
                    self, "ارسال مجدد ایمیل",
                    f"آیا مطمئن هستید که می‌خواهید ایمیل به {email.recipient_name} ارسال مجدد شود؟",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    attachments = [att.file_path for att in email.attachments if os.path.exists(att.file_path)]
                    self.controller.send_email(
                        email.recipient_name, email.recipient_email,
                        email.subject, email.message, attachments
                    )

    def export_sms_data(self):
        """Export SMS data to CSV."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "ذخیره فایل CSV", "sms_data.csv", "CSV Files (*.csv)"
        )
        if file_path:
            if self.controller.export_sms_data(file_path):
                QMessageBox.information(self, "خروجی موفق", "داده‌های پیامک با موفقیت ذخیره شدند.")

    def export_email_data(self):
        """Export Email data to CSV."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "ذخیره فایل CSV", "email_data.csv", "CSV Files (*.csv)"
        )
        if file_path:
            if self.controller.export_email_data(file_path):
                QMessageBox.information(self, "خروجی موفق", "داده‌های ایمیل با موفقیت ذخیره شدند.")

    def show_new_notification_dialog(self):
        """Show new notification dialog."""
        # Create a simple dialog for now
        dialog = NewNotificationDialog(self.controller, self)
        dialog.exec()

    def refresh_data(self):
        """Refresh all data."""
        self.controller.refresh_data()

    def set_loading(self, loading: bool):
        """Set loading state."""
        self.progress_bar.setVisible(loading)
        if loading:
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
        else:
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(1)

    def show_error(self, message: str):
        """Show error message."""
        QMessageBox.critical(self, "خطا", message)

    def update_status(self, message: str):
        """Update status bar."""
        self.status_bar.showMessage(message, 3000)

    @staticmethod
    def get_notification_history_stylesheet() -> str:
        """Return the CSS stylesheet for the NotificationHistoryWidget."""
        return """
        QWidget#NotificationHistoryWidget {
            background-color: #f5f5f5;
            font-family: IranSANS;
        }

        QLabel#titleLabel {
            font-family: IranSANS;
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }

        QPushButton#newNotificationButton {
            background-color: #007acc;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 16px;
            font-family: IranSANS;
            font-size: 14px;
            font-weight: bold;
        }

        QPushButton#newNotificationButton:hover {
            background-color: #005999;
        }

        QPushButton#newNotificationButton:pressed {
            background-color: #004580;
        }

        QPushButton#refreshButton {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 16px;
            font-family: IranSANS;
            font-size: 14px;
            font-weight: bold;
        }

        QPushButton#refreshButton:hover {
            background-color: #2980b9;
        }

        QPushButton#refreshButton:pressed {
            background-color: #21618c;
        }

        QTabWidget {
            background-color: transparent;
            font-family: IranSANS;
        }

        QTabWidget::pane {
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: white;
            margin-top: 2px;
        }

        QTabBar::tab {
            background-color: #f8f9fa;
            color: #495057;
            padding: 10px 20px;
            margin-right: 2px;
            border: 1px solid #dee2e6;
            border-bottom: none;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            font-family: IranSANS;
            font-weight: bold;
            font-size: 14px;
        }

        QTabBar::tab:selected {
            background-color: white;
            color: #2c3e50;
            border-bottom: 2px solid #007acc;
        }

        QTabBar::tab:hover:!selected {
            background-color: #e9ecef;
        }

        QGroupBox {
            font-family: IranSANS;
            font-weight: bold;
            font-size: 14px;
            color: #34495e;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            margin-top: 15px;
            padding-top: 15px;
            background-color: white;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 10px 0 10px;
            background-color: white;
        }

        QLineEdit {
            border: 2px solid #dee2e6;
            border-radius: 5px;
            padding: 8px 12px;
            font-family: IranSANS;
            font-size: 13px;
            background-color: white;
        }

        QLineEdit:focus {
            border-color: #007acc;
            outline: none;
        }

        QComboBox {
            border: 2px solid #dee2e6;
            border-radius: 5px;
            padding: 8px 12px;
            font-family: IranSANS;
            font-size: 13px;
            background-color: white;
            min-width: 100px;
        }

        QComboBox:focus {
            border-color: #007acc;
        }

        QComboBox::drop-down {
            border: none;
            width: 20px;
        }

        QComboBox::down-arrow {
            image: url(down_arrow.png);
            width: 12px;
            height: 12px;
        }

        QDateEdit {
            border: 2px solid #dee2e6;
            border-radius: 5px;
            padding: 8px 12px;
            font-family: IranSANS;
            font-size: 13px;
            background-color: white;
            min-width: 120px;
        }

        QDateEdit:focus {
            border-color: #007acc;
        }

        QPushButton#quickDateButton {
            background-color: #e9ecef;
            color: #495057;
            border: 1px solid #ced4da;
            border-radius: 4px;
            padding: 6px 12px;
            font-family: IranSANS;
            font-size: 12px;
            margin: 2px;
        }

        QPushButton#quickDateButton:hover {
            background-color: #dee2e6;
            color: #212529;
        }

        QPushButton#quickDateButton:pressed {
            background-color: #ced4da;
        }

        QPushButton#filterActionButton {
            background-color: #6c757d;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 6px 12px;
            font-family: IranSANS;
            font-size: 12px;
            margin: 2px;
        }

        QPushButton#filterActionButton:hover {
            background-color: #5a6268;
        }

        QPushButton#exportButton {
            background-color: #28a745;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 6px 12px;
            font-family: IranSANS;
            font-size: 12px;
            font-weight: bold;
        }

        QPushButton#exportButton:hover {
            background-color: #218838;
        }

        QTableWidget#smsTable, QTableWidget#emailTable {
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            selection-background-color: #e3f2fd;
            gridline-color: #f8f9fa;
            font-family: IranSANS;
            font-size: 13px;
        }

        QTableWidget#smsTable::item:selected, QTableWidget#emailTable::item:selected {
            background-color: #e3f2fd;
            color: #1976d2;
        }

        QTableWidget#smsTable::item:alternate, QTableWidget#emailTable::item:alternate {
            background-color: #f8f9fa;
        }

        QHeaderView::section {
            background-color: #f1f3f4;
            color: #2c3e50;
            padding: 12px 8px;
            border: 1px solid #dee2e6;
            border-left: none;
            font-family: IranSANS;
            font-weight: bold;
            font-size: 13px;
        }

        QHeaderView::section:first {
            border-left: 1px solid #dee2e6;
            border-top-left-radius: 8px;
        }

        QHeaderView::section:last {
            border-top-right-radius: 8px;
        }

        QPushButton#paginationButton {
            background-color: #f8f9fa;
            color: #495057;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 6px 12px;
            font-family: IranSANS;
            font-size: 12px;
            min-width: 60px;
        }

        QPushButton#paginationButton:hover:enabled {
            background-color: #e9ecef;
        }

        QPushButton#paginationButton:pressed:enabled {
            background-color: #dee2e6;
        }

        QPushButton#paginationButton:disabled {
            background-color: #f8f9fa;
            color: #adb5bd;
            border-color: #e9ecef;
        }

        QLabel#paginationLabel {
            font-family: IranSANS;
            font-size: 13px;
            color: #495057;
            font-weight: bold;
            margin: 0 10px;
        }

        QLabel#countLabel {
            font-family: IranSANS;
            font-size: 13px;
            color: #6c757d;
            font-weight: normal;
        }

        QStatusBar {
            background-color: #f8f9fa;
            color: #495057;
            border-top: 1px solid #dee2e6;
            font-family: IranSANS;
            font-size: 12px;
        }

        QProgressBar {
            border: 1px solid #dee2e6;
            border-radius: 3px;
            background-color: #f8f9fa;
            text-align: center;
            font-family: IranSANS;
            font-size: 11px;
        }

        QProgressBar::chunk {
            background-color: #007acc;
            border-radius: 2px;
        }

        QMenu {
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 4px 0;
            font-family: IranSANS;
            font-size: 13px;
        }

        QMenu::item {
            padding: 8px 20px;
            color: #495057;
        }

        QMenu::item:selected {
            background-color: #e3f2fd;
            color: #1976d2;
        }

        QMenu::separator {
            height: 1px;
            background-color: #dee2e6;
            margin: 4px 0;
        }
        """


class SMSDetailsDialog(QDialog):
    """Dialog for showing SMS details."""

    def __init__(self, sms: SMSNotification, parent=None):
        super().__init__(parent)
        self.sms = sms
        self.setup_ui()

    def setup_ui(self):
        """Setup dialog UI."""
        self.setWindowTitle("جزئیات پیامک")
        self.setModal(True)
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        # SMS details
        details_layout = QGridLayout()

        details_layout.addWidget(QLabel("نام گیرنده:"), 0, 0)
        details_layout.addWidget(QLabel(self.sms.recipient_name), 0, 1)

        details_layout.addWidget(QLabel("شماره تماس:"), 1, 0)
        details_layout.addWidget(QLabel(self.sms.recipient_phone), 1, 1)

        details_layout.addWidget(QLabel("وضعیت:"), 2, 0)
        status_label = QLabel(NotificationController.get_status_display(self.sms.status))
        details_layout.addWidget(status_label, 2, 1)

        details_layout.addWidget(QLabel("تاریخ ایجاد:"), 3, 0)
        details_layout.addWidget(QLabel(self.sms.created_at.strftime('%Y-%m-%d %H:%M:%S')), 3, 1)

        if self.sms.sent_at:
            details_layout.addWidget(QLabel("تاریخ ارسال:"), 4, 0)
            details_layout.addWidget(QLabel(self.sms.sent_at.strftime('%Y-%m-%d %H:%M:%S')), 4, 1)

        if self.sms.error_message:
            details_layout.addWidget(QLabel("پیام خطا:"), 5, 0)
            error_label = QLabel(self.sms.error_message)
            error_label.setStyleSheet("color: red;")
            error_label.setWordWrap(True)
            details_layout.addWidget(error_label, 5, 1)

        layout.addLayout(details_layout)

        # MessageModel content
        layout.addWidget(QLabel("متن پیام:"))
        message_edit = QTextEdit()
        message_edit.setPlainText(self.sms.message)
        message_edit.setReadOnly(True)
        layout.addWidget(message_edit)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)


class EmailDetailsDialog(QDialog):
    """Dialog for showing Email details."""

    def __init__(self, email: EmailNotification, parent=None):
        super().__init__(parent)
        self.email = email
        self.setup_ui()

    def setup_ui(self):
        """Setup dialog UI."""
        self.setWindowTitle("جزئیات ایمیل")
        self.setModal(True)
        self.resize(600, 500)

        layout = QVBoxLayout(self)

        # Email details
        details_layout = QGridLayout()

        details_layout.addWidget(QLabel("نام گیرنده:"), 0, 0)
        details_layout.addWidget(QLabel(self.email.recipient_name), 0, 1)

        details_layout.addWidget(QLabel("آدرس ایمیل:"), 1, 0)
        details_layout.addWidget(QLabel(self.email.recipient_email), 1, 1)

        details_layout.addWidget(QLabel("موضوع:"), 2, 0)
        subject_label = QLabel(self.email.subject)
        subject_label.setWordWrap(True)
        details_layout.addWidget(subject_label, 2, 1)

        details_layout.addWidget(QLabel("وضعیت:"), 3, 0)
        status_label = QLabel(NotificationController.get_status_display(self.email.status))
        details_layout.addWidget(status_label, 3, 1)

        details_layout.addWidget(QLabel("تاریخ ایجاد:"), 4, 0)
        details_layout.addWidget(QLabel(self.email.created_at.strftime('%Y-%m-%d %H:%M:%S')), 4, 1)

        if self.email.sent_at:
            details_layout.addWidget(QLabel("تاریخ ارسال:"), 5, 0)
            details_layout.addWidget(QLabel(self.email.sent_at.strftime('%Y-%m-%d %H:%M:%S')), 5, 1)

        if self.email.error_message:
            details_layout.addWidget(QLabel("پیام خطا:"), 6, 0)
            error_label = QLabel(self.email.error_message)
            error_label.setStyleSheet("color: red;")
            error_label.setWordWrap(True)
            details_layout.addWidget(error_label, 6, 1)

        layout.addLayout(details_layout)

        # Attachments
        if self.email.attachments:
            layout.addWidget(QLabel("فایل‌های پیوست:"))
            attachments_list = QListWidget()
            for attachment in self.email.attachments:
                item_text = f"{attachment.filename} ({attachment.file_size} بایت)"
                item = QListWidgetItem(item_text)
                item.setToolTip(attachment.file_path)
                attachments_list.addItem(item)
            attachments_list.setMaximumHeight(100)
            layout.addWidget(attachments_list)

        # MessageModel content
        layout.addWidget(QLabel("متن ایمیل:"))
        message_edit = QTextEdit()
        message_edit.setPlainText(self.email.message)
        message_edit.setReadOnly(True)
        layout.addWidget(message_edit)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)


class NewNotificationDialog(QDialog):
    """Dialog for creating new notifications."""

    def __init__(self, controller: NotificationController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.uploaded_files = []
        self.setup_ui()

    def setup_ui(self):
        """Setup dialog UI."""
        self.setWindowTitle("ارسال اطلاعیه جدید")
        self.setModal(True)
        self.resize(600, 500)

        layout = QVBoxLayout(self)

        # Create tab widget
        self.tab_widget = QTabWidget()

        # SMS Tab
        sms_tab = self.create_sms_tab()
        self.tab_widget.addTab(sms_tab, "پیامک")

        # Email Tab
        email_tab = self.create_email_tab()
        self.tab_widget.addTab(email_tab, "ایمیل")

        layout.addWidget(self.tab_widget)

        # Buttons
        button_layout = QHBoxLayout()

        send_btn = QPushButton("ارسال")
        send_btn.clicked.connect(self.send_notification)

        cancel_btn = QPushButton("لغو")
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(send_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def create_sms_tab(self):
        """Create SMS tab content."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Name field
        layout.addWidget(QLabel("نام مشتری:"))
        self.sms_name_edit = QLineEdit()
        self.sms_name_edit.setPlaceholderText("نام مشتری را وارد کنید...")
        layout.addWidget(self.sms_name_edit)

        # Phone field
        layout.addWidget(QLabel("شماره تماس:"))
        self.sms_phone_edit = QLineEdit()
        self.sms_phone_edit.setPlaceholderText("09123456789")
        layout.addWidget(self.sms_phone_edit)

        # MessageModel field
        layout.addWidget(QLabel("متن پیام:"))
        self.sms_text_edit = QTextEdit()
        self.sms_text_edit.setPlaceholderText("متن پیام خود را اینجا وارد کنید...")
        layout.addWidget(self.sms_text_edit)

        return widget

    def create_email_tab(self):
        """Create Email tab content."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Name field
        layout.addWidget(QLabel("نام مشتری:"))
        self.email_name_edit = QLineEdit()
        self.email_name_edit.setPlaceholderText("نام مشتری را وارد کنید...")
        layout.addWidget(self.email_name_edit)

        # Email field
        layout.addWidget(QLabel("آدرس ایمیل:"))
        self.email_address_edit = QLineEdit()
        self.email_address_edit.setPlaceholderText("example@domain.com")
        layout.addWidget(self.email_address_edit)

        # Subject field
        layout.addWidget(QLabel("موضوع:"))
        self.email_subject_edit = QLineEdit()
        self.email_subject_edit.setPlaceholderText("موضوع ایمیل را وارد کنید...")
        layout.addWidget(self.email_subject_edit)

        # MessageModel field
        layout.addWidget(QLabel("متن ایمیل:"))
        self.email_text_edit = QTextEdit()
        self.email_text_edit.setPlaceholderText("متن ایمیل خود را اینجا وارد کنید...")
        layout.addWidget(self.email_text_edit)

        # File upload section
        layout.addWidget(QLabel("فایل‌های پیوست:"))

        file_layout = QHBoxLayout()
        upload_btn = QPushButton("انتخاب فایل")
        upload_btn.clicked.connect(self.upload_files)
        file_layout.addWidget(upload_btn)

        remove_btn = QPushButton("حذف فایل انتخابی")
        remove_btn.clicked.connect(self.remove_selected_file)
        file_layout.addWidget(remove_btn)

        clear_all_btn = QPushButton("حذف همه فایل‌ها")
        clear_all_btn.clicked.connect(self.clear_all_files)
        file_layout.addWidget(clear_all_btn)

        self.file_count_label = QLabel("هیچ فایلی انتخاب نشده")
        file_layout.addWidget(self.file_count_label)

        layout.addLayout(file_layout)

        # File list
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(100)
        layout.addWidget(self.file_list)

        return widget

    def upload_files(self):
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
                self.update_file_list()

            if len(new_files) < len(files):
                QMessageBox.information(
                    self,
                    "فایل‌های تکراری",
                    "برخی فایل‌ها قبلاً انتخاب شده‌اند و نادیده گرفته شدند."
                )

    def remove_selected_file(self):
        """Remove selected file from the list."""
        current_row = self.file_list.currentRow()
        if current_row >= 0:
            removed_file = self.uploaded_files.pop(current_row)
            self.update_file_list()
            QMessageBox.information(
                self,
                "حذف فایل",
                f"فایل '{os.path.basename(removed_file)}' حذف شد."
            )
        else:
            QMessageBox.warning(self, "خطا", "لطفاً فایلی را برای حذف انتخاب کنید.")

    def clear_all_files(self):
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
                self.update_file_list()
                QMessageBox.information(self, "حذف فایل‌ها", "همه فایل‌ها حذف شدند.")

    def update_file_list(self):
        """Update the file list display."""
        self.file_list.clear()

        for file_path in self.uploaded_files:
            file_name = os.path.basename(file_path)
            item = QListWidgetItem(file_name)
            item.setToolTip(file_path)
            self.file_list.addItem(item)

        count = len(self.uploaded_files)
        if count == 0:
            self.file_count_label.setText("هیچ فایلی انتخاب نشده")
        else:
            self.file_count_label.setText(f"{count} فایل انتخاب شده")

    def send_notification(self):
        """Send notification based on active tab."""
        current_tab = self.tab_widget.currentIndex()

        if current_tab == 0:  # SMS tab
            self.send_sms()
        else:  # Email tab
            self.send_email()

    def send_sms(self):
        """Send SMS notification."""
        name = self.sms_name_edit.text().strip()
        phone = self.sms_phone_edit.text().strip()
        message = self.sms_text_edit.toPlainText().strip()

        if not name:
            QMessageBox.warning(self, "خطا", "نام مشتری وارد نشده است")
            return

        if not phone:
            QMessageBox.warning(self, "خطا", "شماره تماس وارد نشده است")
            return

        if not message:
            QMessageBox.warning(self, "خطا", "متن پیام وارد نشده است")
            return

        if self.controller.send_sms(name, phone, message):
            QMessageBox.information(self, "موفقیت", "پیامک با موفقیت ارسال شد")
            self.accept()

    def send_email(self):
        """Send email notification."""
        name = self.email_name_edit.text().strip()
        email = self.email_address_edit.text().strip()
        subject = self.email_subject_edit.text().strip()
        message = self.email_text_edit.toPlainText().strip()

        if not name:
            QMessageBox.warning(self, "خطا", "نام مشتری وارد نشده است")
            return

        if not email:
            QMessageBox.warning(self, "خطا", "آدرس ایمیل وارد نشده است")
            return

        if not subject:
            QMessageBox.warning(self, "خطا", "موضوع ایمیل وارد نشده است")
            return

        if not message:
            QMessageBox.warning(self, "خطا", "متن ایمیل وارد نشده است")
            return

        if self.controller.send_email(name, email, subject, message, self.uploaded_files):
            QMessageBox.information(self, "موفقیت", "ایمیل با موفقیت ارسال شد")
            self.accept()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication([])
    window = NotificationHistoryWidget()
    window.show()
    sys.exit(app.exec())
