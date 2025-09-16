import sys
import os
import sqlite3
import bcrypt
from datetime import datetime
from PySide6.QtWidgets import (
    QInputDialog, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QComboBox, QDateEdit, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QTabWidget, QWidget, QMessageBox,
    QHeaderView, QSplitter, QGroupBox, QCheckBox, QFileDialog, QFrame,
    QScrollArea
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QPixmap, QIcon, QFont
from modules.helper_functions import to_persian_number
from databases.users import get_user_session_stats


class PasswordChangeDialog(QDialog):
    def __init__(self, username, dp_path, parent=None):
        super().__init__(parent)
        self.username = username
        self.db_path = dp_path
        self.setWindowTitle(f"تغییر رمز عبور - {username}")
        self.setModal(True)
        self.resize(350, 250)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title = QLabel(f"تغییر رمز عبور برای: {self.username}")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form_layout = QFormLayout()

        self.current_password = QLineEdit()
        self.current_password.setEchoMode(QLineEdit.Password)
        self.current_password.setPlaceholderText("رمز عبور فعلی را وارد کنید")
        form_layout.addRow("رمز عبور فعلی:", self.current_password)

        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        self.new_password.setPlaceholderText("رمز عبور جدید (حداقل 6 کاراکتر)")
        form_layout.addRow("رمز عبور جدید:", self.new_password)

        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.confirm_password.setPlaceholderText("تکرار رمز عبور جدید")
        form_layout.addRow("تأیید رمز عبور:", self.confirm_password)

        layout.addLayout(form_layout)

        # Password strength indicator
        self.strength_label = QLabel("قدرت رمز عبور: ")
        self.strength_label.setStyleSheet("color: gray;")
        layout.addWidget(self.strength_label)

        # Connect password field to strength checker
        self.new_password.textChanged.connect(self.check_password_strength)

        # Buttons
        button_layout = QHBoxLayout()

        self.save_btn = QPushButton("تغییر رمز عبور")
        self.save_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px; }")
        self.save_btn.clicked.connect(self.change_password)

        self.cancel_btn = QPushButton("انصراف")
        self.cancel_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; padding: 8px; }")
        self.cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def check_password_strength(self, password):
        if len(password) < 6:
            self.strength_label.setText("قدرت رمز عبور: ضعیف")
            self.strength_label.setStyleSheet("color: red;")
        elif len(password) < 8:
            self.strength_label.setText("قدرت رمز عبور: متوسط")
            self.strength_label.setStyleSheet("color: orange;")
        else:
            self.strength_label.setText("قدرت رمز عبور: قوی")
            self.strength_label.setStyleSheet("color: green;")

    def change_password(self):
        current_pwd = self.current_password.text()
        new_pwd = self.new_password.text()
        confirm_pwd = self.confirm_password.text()

        if not all([current_pwd, new_pwd, confirm_pwd]):
            QMessageBox.warning(self, "خطا", "تمام فیلدها الزامی هستند!")
            return

        if new_pwd != confirm_pwd:
            QMessageBox.warning(self, "خطا", "رمز عبور جدید و تأیید آن یکسان نیستند!")
            return

        if len(new_pwd) < 6:
            QMessageBox.warning(self, "خطا", "رمز عبور باید حداقل 6 کاراکتر باشد!")
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Verify current password
                cursor.execute("SELECT password_hash FROM users WHERE username = ?", (self.username,))
                result = cursor.fetchone()

                if not result or not bcrypt.checkpw(current_pwd.encode(), result[0]):
                    QMessageBox.warning(self, "خطا", "رمز عبور فعلی صحیح نیست!")
                    return

                # Hash new password and update
                new_hash = bcrypt.hashpw(new_pwd.encode(), bcrypt.gensalt())
                cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?",
                               (new_hash, self.username))
                conn.commit()

                QMessageBox.information(self, "موفقیت", "رمز عبور با موفقیت تغییر یافت!")
                self.accept()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای دیتابیس", f"خطا در تغییر رمز عبور: {e}")


class UserManagementWidget(QWidget):
    user_updated = Signal()

    def __init__(self, parent, dp_path):
        super().__init__(parent)
        self.current_user = None
        self.avatar_path = None
        self.db_path = dp_path
        self.setWindowTitle("مدیریت کاربران")
        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - UsersModel list
        left_panel = self.create_user_list_panel()

        # Right panel - UsersModel details
        right_panel = self.create_user_details_panel()

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 800])

        main_layout.addWidget(splitter)

    def create_user_list_panel(self):
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Header
        header = QLabel("لیست کاربران")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("QLabel { background-color: #2196F3; color: white; padding: 10px; }")
        left_layout.addWidget(header)

        # UsersModel list controls
        controls_layout = QHBoxLayout()

        self.add_user_btn = QPushButton("افزودن کاربر جدید")
        self.add_user_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px; }")
        self.add_user_btn.clicked.connect(self.add_new_user)

        self.delete_btn = QPushButton("حذف کاربر")
        self.delete_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; padding: 8px; }")
        self.delete_btn.clicked.connect(self.delete_user)
        self.delete_btn.setEnabled(False)

        controls_layout.addWidget(self.add_user_btn)
        controls_layout.addWidget(self.delete_btn)

        left_layout.addLayout(controls_layout)

        # Search functionality
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("جستجو بر اساس نام کاربری یا نام کامل...")
        self.search_input.textChanged.connect(self.filter_users)

        search_btn = QPushButton("جستجو")
        search_btn.clicked.connect(self.filter_users)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        left_layout.addLayout(search_layout)

        # Users table
        self.users_table = QTableWidget()
        self.users_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.selectionModel().selectionChanged.connect(self.on_user_selected)
        left_layout.addWidget(self.users_table)

        # Statistics
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 5px; }")
        left_layout.addWidget(self.stats_label)

        return left_panel

    def create_user_details_panel(self):
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Header
        header = QLabel("جزئیات کاربر")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("QLabel { background-color: #673AB7; color: white; padding: 10px; }")
        right_layout.addWidget(header)

        # Scroll area for form
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Tab widget for different sections
        self.tab_widget = QTabWidget()

        # Basic Info Tab
        self.basic_info_tab = self.create_basic_info_tab()
        self.tab_widget.addTab(self.basic_info_tab, "اطلاعات پایه")

        # Profile Tab
        self.profile_tab = self.create_profile_tab()
        self.tab_widget.addTab(self.profile_tab, "پروفایل کاربری")

        # Activity Tab
        self.activity_tab = self.create_activity_tab()
        self.tab_widget.addTab(self.activity_tab, "فعالیت کاربر")

        scroll_layout.addWidget(self.tab_widget)

        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        right_layout.addWidget(scroll_area)

        # Action buttons
        self.create_action_buttons(right_layout)

        return right_panel

    def create_basic_info_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # UsersModel account group
        account_group = QGroupBox("حساب کاربری")
        account_layout = QFormLayout(account_group)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("نام کاربری یکتا")

        # Role mapping: Persian display -> English value
        self.role_mapping = {
            'مدیر سیستم': 'admin',
            'مترجم': 'translator',
            'منشی': 'clerk',
            'حسابدار': 'accountant'
        }

        self.role_combo = QComboBox()
        self.role_combo.addItems(list(self.role_mapping.keys()))

        account_layout.addRow("نام کاربری:", self.username_edit)
        account_layout.addRow("نقش:", self.role_combo)

        layout.addWidget(account_group)

        # Date information group
        date_group = QGroupBox("اطلاعات تاریخ")
        date_layout = QFormLayout(date_group)

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy/MM/dd")

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy/MM/dd")

        date_layout.addRow("تاریخ شروع:", self.start_date_edit)
        date_layout.addRow("تاریخ پایان:", self.end_date_edit)

        layout.addWidget(date_group)
        layout.addStretch()

        return tab

    def create_profile_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Personal info group
        personal_group = QGroupBox("اطلاعات شخصی")
        personal_layout = QFormLayout(personal_group)

        self.full_name_edit = QLineEdit()
        self.full_name_edit.setPlaceholderText("نام و نام خانوادگی")

        self.role_fa_edit = QLineEdit()
        self.role_fa_edit.setPlaceholderText("عنوان شغلی به فارسی")

        self.birth_date_edit = QDateEdit()
        self.birth_date_edit.setCalendarPopup(True)
        self.birth_date_edit.setDisplayFormat("yyyy/MM/dd")
        self.birth_date_edit.setSpecialValueText("تاریخ تولد تعین نشده")
        self.birth_date_edit.setDate(QDate(1900, 1, 1))

        self.national_id_edit = QLineEdit()
        self.national_id_edit.setPlaceholderText("کد ملی")

        personal_layout.addRow("نام کامل:", self.full_name_edit)
        personal_layout.addRow("عنوان شغلی:", self.role_fa_edit)
        personal_layout.addRow("تاریخ تولد:", self.birth_date_edit)
        personal_layout.addRow("کد ملی:", self.national_id_edit)

        layout.addWidget(personal_group)

        # Contact info group
        contact_group = QGroupBox("اطلاعات تماس")
        contact_layout = QFormLayout(contact_group)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("example@domain.com")

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("09xxxxxxxxx")

        contact_layout.addRow("ایمیل:", self.email_edit)
        contact_layout.addRow("تلفن همراه:", self.phone_edit)

        layout.addWidget(contact_group)

        # Additional info group
        additional_group = QGroupBox("اطلاعات تکمیلی")
        additional_layout = QVBoxLayout(additional_group)

        # Address
        address_layout = QFormLayout()
        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(80)
        self.address_edit.setPlaceholderText("آدرس کامل...")
        address_layout.addRow("آدرس:", self.address_edit)
        additional_layout.addLayout(address_layout)

        # Bio
        bio_layout = QFormLayout()
        self.bio_edit = QTextEdit()
        self.bio_edit.setMaximumHeight(100)
        self.bio_edit.setPlaceholderText("بیوگرافی و توضیحات اضافی...")
        bio_layout.addRow("بیوگرافی:", self.bio_edit)
        additional_layout.addLayout(bio_layout)

        layout.addWidget(additional_group)

        # Avatar section
        avatar_group = QGroupBox("تصویر پروفایل")
        avatar_layout = QHBoxLayout(avatar_group)

        self.avatar_label = QLabel("بدون تصویر")
        self.avatar_label.setFixedSize(120, 120)
        self.avatar_label.setStyleSheet("""
            QLabel { 
                border: 2px dashed #ccc; 
                text-align: center;
                background-color: #f9f9f9;
            }
        """)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        avatar_buttons = QVBoxLayout()
        self.select_avatar_btn = QPushButton("انتخاب تصویر")
        self.select_avatar_btn.clicked.connect(self.select_avatar)

        self.clear_avatar_btn = QPushButton("حذف تصویر")
        self.clear_avatar_btn.clicked.connect(self.clear_avatar)

        avatar_buttons.addWidget(self.select_avatar_btn)
        avatar_buttons.addWidget(self.clear_avatar_btn)
        avatar_buttons.addStretch()

        avatar_layout.addWidget(self.avatar_label)
        avatar_layout.addLayout(avatar_buttons)
        avatar_layout.addStretch()

        layout.addWidget(avatar_group)
        layout.addStretch()

        return tab

    def create_activity_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Login history
        history_group = QGroupBox("تاریخچه ورود")
        history_layout = QVBoxLayout(history_group)

        self.login_history_table = QTableWidget()
        self.login_history_table.setMaximumHeight(200)
        history_layout.addWidget(self.login_history_table)

        layout.addWidget(history_group)

        # UsersModel statistics
        stats_group = QGroupBox("آمار کاربر")
        stats_layout = QFormLayout(stats_group)

        self.total_logins_label = QLabel("0")
        self.session_stats_label = QLabel("آمار موجود نیست")
        self.account_age_label = QLabel("0 روز")

        stats_layout.addRow("تعداد کل ورودها:", self.total_logins_label)
        stats_layout.addRow("آمار جلسات (30 روز اخیر):", self.session_stats_label)
        stats_layout.addRow("قدمت حساب:", self.account_age_label)

        layout.addWidget(stats_group)
        layout.addStretch()

        return tab

    def create_action_buttons(self, layout):
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        button_layout = QHBoxLayout()

        self.save_btn = QPushButton("ذخیره تغییرات")
        self.save_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; padding: 10px; font-weight: bold; }")
        self.save_btn.clicked.connect(self.save_user)
        self.save_btn.setEnabled(False)

        self.change_pwd_btn = QPushButton("تغییر رمز عبور")
        self.change_pwd_btn.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; padding: 10px; font-weight: bold; }")
        self.change_pwd_btn.clicked.connect(self.change_password)
        self.change_pwd_btn.setEnabled(False)

        self.end_cooperation_btn = QPushButton("پایان همکاری")
        self.end_cooperation_btn.setStyleSheet(
            "QPushButton { background-color: #795548; color: white; padding: 10px; font-weight: bold; }")
        self.end_cooperation_btn.clicked.connect(self.end_cooperation)
        self.end_cooperation_btn.setEnabled(False)

        self.cancel_btn = QPushButton("انصراف")
        self.cancel_btn.setStyleSheet("QPushButton { background-color: #9E9E9E; color: white; padding: 10px; }")
        self.cancel_btn.clicked.connect(self.cancel_changes)

        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.change_pwd_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.end_cooperation_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def get_persian_role(self, english_role):
        """Convert English role to Persian display"""
        role_reverse_mapping = {
            'admin': 'مدیر سیستم',
            'translator': 'مترجم',
            'clerk': 'منشی',
            'accountant': 'حسابدار'
        }
        return role_reverse_mapping.get(english_role, english_role)

    def load_users(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT u.username, 
                           COALESCE(up.full_name, '') as full_name,
                           COALESCE(up.role_fa, '') as role_fa,
                           u.role as english_role
                    FROM users u
                    LEFT JOIN user_profiles up ON u.username = up.username
                    ORDER BY u.username
                """)

                self.all_users = cursor.fetchall()
                self.display_users(self.all_users)
                self.update_statistics()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای دیتابیس", f"خطا در بارگذاری کاربران: {e}")

    def display_users(self, users):
        self.users_table.setRowCount(len(users))
        self.users_table.setColumnCount(3)
        self.users_table.setHorizontalHeaderLabels([
            "نام کاربری", "نام کامل", "نقش"
        ])

        for row, user in enumerate(users):
            # Username
            item = QTableWidgetItem(user[0])
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.users_table.setItem(row, 0, item)

            # Full name
            item = QTableWidgetItem(user[1] or "")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.users_table.setItem(row, 1, item)

            # Role (Persian)
            role_display = user[2] if user[2] else self.get_persian_role(user[3])
            item = QTableWidgetItem(role_display)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.users_table.setItem(row, 2, item)

        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def filter_users(self):
        search_text = self.search_input.text().lower()
        if not search_text:
            self.display_users(self.all_users)
            return

        filtered_users = [
            user for user in self.all_users
            if search_text in user[0].lower() or search_text in (user[1] or '').lower()
        ]
        self.display_users(filtered_users)

    def update_statistics(self):
        total_users = len(self.all_users)

        # Get active/inactive count from database
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users WHERE active = 1")
                active_users = cursor.fetchone()[0]
                inactive_users = total_users - active_users
        except:
            active_users = 0
            inactive_users = 0

        self.stats_label.setText(
            f"کل کاربران: {total_users} | فعال: {active_users} | غیرفعال: {inactive_users}"
        )

    def on_user_selected(self):
        selection = self.users_table.selectionModel().selectedRows()
        if not selection:
            self.clear_form()
            return

        row = selection[0].row()
        username = self.users_table.item(row, 0).text()
        self.load_user_details(username)

        # Enable delete button
        self.delete_btn.setEnabled(username != 'admin')

    def load_user_details(self, username):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Load user basic info
                cursor.execute("""
                    SELECT username, role, active, start_date, end_date
                    FROM users WHERE username = ?
                """, (username,))
                user_data = cursor.fetchone()

                if not user_data:
                    return

                # Load user profile
                cursor.execute("""
                    SELECT full_name, role_fa, date_of_birth, email, phone, 
                           national_id, address, bio, avatar_path
                    FROM user_profiles WHERE username = ?
                """, (username,))
                profile_data = cursor.fetchone()

                # Load login history
                self.load_user_activity(username)

                self.populate_form(user_data, profile_data)
                self.current_user = username

                # Enable buttons
                self.save_btn.setEnabled(True)
                self.change_pwd_btn.setEnabled(True)
                self.end_cooperation_btn.setEnabled(user_data[2])  # Only if user is active

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای دیتابیس", f"خطا در بارگذاری جزئیات کاربر: {e}")

    def load_user_activity(self, username):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Load recent login history
                cursor.execute("""
                    SELECT login_time, logout_time, status, time_on_app
                    FROM login_logs 
                    WHERE username = ?
                    ORDER BY login_time DESC
                    LIMIT 10
                """, (username,))

                history = cursor.fetchall()

                self.login_history_table.setRowCount(len(history))
                self.login_history_table.setColumnCount(4)
                self.login_history_table.setHorizontalHeaderLabels([
                    "زمان ورود", "زمان خروج", "وضعیت", "مدت کار"
                ])

                for row, record in enumerate(history):
                    for col, value in enumerate(record):
                        if col == 3 and value:  # time_on_app column
                            # Convert seconds to minutes and format
                            minutes = round(value / 60, 2)
                            display_value = f"{minutes} دقیقه"
                        else:
                            display_value = str(value) if value else ""

                        item = QTableWidgetItem(display_value)
                        self.login_history_table.setItem(row, col, item)

                # Load statistics
                cursor.execute("SELECT COUNT(*) FROM login_logs WHERE username = ? AND status = 'success'", (username,))
                total_logins = cursor.fetchone()[0]

                # Get session statistics
                session_stats = get_user_session_stats(username, 30)
                if session_stats:
                    stats_text = (f"ورودها: {to_persian_number(session_stats['total_logins'])} | "
                                  f"میانگین هر ورود: {to_persian_number(session_stats['avg_time_minutes'])} دقیقه | "
                                  f"مجموع زمان در برنامه: {to_persian_number(session_stats['total_time_hours'])} ساعت")
                else:
                    stats_text = "آمار موجود نیست"

                cursor.execute("SELECT start_date FROM users WHERE username = ?", (username,))
                start_date_result = cursor.fetchone()
                if start_date_result and start_date_result[0]:
                    start_date = datetime.strptime(start_date_result[0], "%Y-%m-%d")
                    account_age = (datetime.now() - start_date).days
                else:
                    account_age = 0

                self.total_logins_label.setText(str(total_logins))
                self.session_stats_label.setText(stats_text)
                self.account_age_label.setText(f"{account_age} روز")

        except sqlite3.Error as e:
            print(f"Error loading user activity: {e}")

    def populate_form(self, user_data, profile_data):
        # Basic info
        self.username_edit.setText(user_data[0])

        # Set role combo based on English role
        persian_role = self.get_persian_role(user_data[1])
        index = self.role_combo.findText(persian_role)
        if index >= 0:
            self.role_combo.setCurrentIndex(index)

        if user_data[3]:  # start_date
            self.start_date_edit.setDate(QDate.fromString(user_data[3], Qt.DateFormat.ISODate))

        if user_data[4]:  # end_date
            self.end_date_edit.setDate(QDate.fromString(user_data[4], Qt.DateFormat.ISODate))
        else:
            self.end_date_edit.setDate(QDate.currentDate())

        # Profile info
        if profile_data:
            self.full_name_edit.setText(profile_data[0] or "")
            self.role_fa_edit.setText(profile_data[1] or "")

            if profile_data[2]:  # date_of_birth
                self.birth_date_edit.setDate(QDate.fromString(profile_data[2], Qt.DateFormat.ISODate))
            else:
                self.birth_date_edit.setDate(QDate(1900, 1, 1))

            self.email_edit.setText(profile_data[3] or "")
            self.phone_edit.setText(profile_data[4] or "")
            self.national_id_edit.setText(profile_data[5] or "")
            self.address_edit.setPlainText(profile_data[6] or "")
            self.bio_edit.setPlainText(profile_data[7] or "")

            # Load avatar
            if profile_data[8] and os.path.exists(profile_data[8]):
                self.avatar_path = profile_data[8]
                self.load_avatar(profile_data[8])
            else:
                self.clear_avatar()
        else:
            self.clear_profile_form()

    def clear_profile_form(self):
        """Clear all profile form fields"""
        self.full_name_edit.clear()
        self.role_fa_edit.clear()
        self.birth_date_edit.setDate(QDate(1900, 1, 1))
        self.email_edit.clear()
        self.phone_edit.clear()
        self.national_id_edit.clear()
        self.address_edit.clear()
        self.bio_edit.clear()
        self.clear_avatar()

    def clear_form(self):
        """Clear all form fields"""
        self.current_user = None
        self.avatar_path = None

        # Basic info
        self.username_edit.clear()
        self.role_combo.setCurrentIndex(0)
        self.start_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setDate(QDate.currentDate())

        # Profile info
        self.clear_profile_form()

        # Activity
        self.login_history_table.setRowCount(0)
        self.total_logins_label.setText("0")
        self.last_login_label.setText("هرگز")
        self.account_age_label.setText("0 روز")

        # Disable buttons
        self.save_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.change_pwd_btn.setEnabled(False)
        self.end_cooperation_btn.setEnabled(False)

    def select_avatar(self):
        """Select avatar image file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "انتخاب تصویر پروفایل",
            "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp)"
        )

        if file_path:
            self.avatar_path = file_path
            self.load_avatar(file_path)

    def load_avatar(self, file_path):
        """Load and display avatar image"""
        try:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                # Scale image to fit label
                scaled_pixmap = pixmap.scaled(
                    self.avatar_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.avatar_label.setPixmap(scaled_pixmap)
                self.avatar_label.setText("")
            else:
                QMessageBox.warning(self, "خطا", "فایل تصویر معتبر نیست")
        except Exception as e:
            QMessageBox.warning(self, "خطا", f"خطا در بارگذاری تصویر: {e}")

    def clear_avatar(self):
        """Clear avatar image"""
        self.avatar_path = None
        self.avatar_label.clear()
        self.avatar_label.setText("بدون تصویر")

    def add_new_user(self):
        """Add new user"""
        self.clear_form()
        self.username_edit.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.current_user = None  # Indicates new user
        self.tab_widget.setCurrentIndex(0)  # Switch to basic info tab

    def save_user(self):
        """Save user data"""
        try:
            # Validate required fields
            username = self.username_edit.text().strip()
            if not username:
                QMessageBox.warning(self, "خطا", "نام کاربری الزامی است")
                return

            # Get English role from Persian selection
            persian_role = self.role_combo.currentText()
            role = self.role_mapping.get(persian_role, 'clerk')

            active = True  # New users are always active
            start_date = self.start_date_edit.date().toString(Qt.DateFormat.ISODate)
            end_date = None

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                if self.current_user is None:  # New user
                    # Check if username already exists
                    cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
                    if cursor.fetchone():
                        QMessageBox.warning(self, "خطا", "نام کاربری قبلاً وجود دارد")
                        return

                    # Create default password dialog
                    password, ok = QInputDialog.getText(
                        self, "رمز عبور", "رمز عبور پیش‌فرض برای کاربر جدید:",
                        text="123456"
                    )
                    if not ok:
                        return

                    # Insert new user
                    cursor.execute("""
                        INSERT INTO users (username, password, role, active, start_date, end_date)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (username, password, role, active, start_date, end_date))

                else:  # Update existing user
                    cursor.execute("""
                        UPDATE users SET role = ?, start_date = ?
                        WHERE username = ?
                    """, (role, start_date, self.current_user))

                # Save profile data
                self.save_user_profile(cursor, username)

                conn.commit()

                QMessageBox.information(self, "موفقیت", "اطلاعات کاربر با موفقیت ذخیره شد")
                self.current_user = username
                self.username_edit.setEnabled(False)
                self.load_users()
                self.user_updated.emit()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای دیتابیس", f"خطا در ذخیره اطلاعات کاربر: {e}")

    def save_user_profile(self, cursor, username):
        """Save user profile information"""
        full_name = self.full_name_edit.text().strip()
        role_fa = self.role_fa_edit.text().strip()

        birth_date = None
        if self.birth_date_edit.date() != QDate(1900, 1, 1):
            birth_date = self.birth_date_edit.date().toString(Qt.DateFormat.ISODate)

        email = self.email_edit.text().strip()
        phone = self.phone_edit.text().strip()
        national_id = self.national_id_edit.text().strip()
        address = self.address_edit.toPlainText().strip()
        bio = self.bio_edit.toPlainText().strip()

        # Handle avatar path
        avatar_path = None
        if self.avatar_path and os.path.exists(self.avatar_path):
            # Copy avatar to application directory if it's not already there
            avatars_dir = os.path.join(os.path.dirname(self.db_path), "avatars")
            os.makedirs(avatars_dir, exist_ok=True)

            if not self.avatar_path.startswith(avatars_dir):
                # Copy file to avatars directory
                file_ext = os.path.splitext(self.avatar_path)[1]
                new_filename = f"{username}_avatar{file_ext}"
                new_path = os.path.join(avatars_dir, new_filename)

                try:
                    import shutil
                    shutil.copy2(self.avatar_path, new_path)
                    avatar_path = new_path
                except Exception as e:
                    print(f"Error copying avatar: {e}")
                    avatar_path = self.avatar_path
            else:
                avatar_path = self.avatar_path

        # Check if profile exists
        cursor.execute("SELECT username FROM user_profiles WHERE username = ?", (username,))

        if cursor.fetchone():
            # Update existing profile
            cursor.execute("""
                    UPDATE user_profiles SET 
                        full_name = ?, role_fa = ?, date_of_birth = ?, email = ?, 
                        phone = ?, national_id = ?, address = ?, bio = ?, avatar_path = ?
                    WHERE username = ?
                """, (full_name, role_fa, birth_date, email, phone, national_id,
                      address, bio, avatar_path, username))
        else:
            # Insert new profile
            cursor.execute("""
                    INSERT INTO user_profiles 
                    (username, full_name, role_fa, date_of_birth, email, phone, 
                     national_id, address, bio, avatar_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (username, full_name, role_fa, birth_date, email, phone,
                      national_id, address, bio, avatar_path))

    def change_password(self):
        """Change user password"""
        if not self.current_user:
            return

        dialog = PasswordChangeDialog(self, self.current_user)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_password = dialog.get_new_password()

            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE users SET password = ? WHERE username = ?",
                        (new_password, self.current_user)
                    )
                    conn.commit()

                QMessageBox.information(self, "موفقیت", "رمز عبور با موفقیت تغییر یافت")

            except sqlite3.Error as e:
                QMessageBox.critical(self, "خطای دیتابیس", f"خطا در تغییر رمز عبور: {e}")

    def end_cooperation(self):
        """End user cooperation (deactivate user)"""
        if not self.current_user:
            return

        reply = QMessageBox.question(
            self, "تأیید پایان همکاری",
            f"آیا مطمئن هستید که می‌خواهید همکاری کاربر '{self.current_user}' را پایان دهید؟\n"
            "این کاربر غیرفعال خواهد شد و نمی‌تواند وارد سیستم شود.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                            UPDATE users SET active = 0, end_date = ?
                            WHERE username = ?
                        """, (datetime.now().strftime("%Y-%m-%d"), self.current_user))
                    conn.commit()

                QMessageBox.information(self, "موفقیت", "همکاری کاربر با موفقیت پایان یافت")
                self.load_users()
                self.load_user_details(self.current_user)  # Refresh details
                self.user_updated.emit()

            except sqlite3.Error as e:
                QMessageBox.critical(self, "خطای دیتابیس", f"خطا در پایان همکاری: {e}")

    def delete_user(self):
        """Delete selected user"""
        if not self.current_user or self.current_user == 'admin':
            return

        reply = QMessageBox.question(
            self, "تأیید حذف کاربر",
            f"آیا مطمئن هستید که می‌خواهید کاربر '{self.current_user}' را حذف کنید؟\n"
            "این عمل غیرقابل بازگشت است و تمام اطلاعات کاربر حذف خواهد شد.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    # Delete related records first
                    cursor.execute("DELETE FROM user_profiles WHERE username = ?", (self.current_user,))
                    cursor.execute("DELETE FROM login_logs WHERE username = ?", (self.current_user,))
                    cursor.execute("DELETE FROM users WHERE username = ?", (self.current_user,))

                    conn.commit()

                # Clean up avatar file
                if self.avatar_path and os.path.exists(self.avatar_path):
                    try:
                        os.remove(self.avatar_path)
                    except:
                        pass

                QMessageBox.information(self, "موفقیت", "کاربر با موفقیت حذف شد")
                self.clear_form()
                self.load_users()
                self.user_updated.emit()

            except sqlite3.Error as e:
                QMessageBox.critical(self, "خطای دیتابیس", f"خطا در حذف کاربر: {e}")

    def cancel_changes(self):
        """Cancel changes and clear form"""
        if self.current_user:
            self.load_user_details(self.current_user)
        else:
            self.clear_form()

    def closeEvent(self, event):
        """Handle window close event"""
        event.accept()
