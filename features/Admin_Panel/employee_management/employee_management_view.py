# features/Admin_Panel/employee_management/employee_management_view.py

import qtawesome as qta
import re
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QLabel, QMessageBox, QDialog, QFormLayout, QComboBox, QDateEdit, QCheckBox
)
from PySide6.QtCore import Signal, Qt, QDate
from PySide6.QtGui import QFont

# Constants
ROLE_MAP = {"admin": "مدیر", "clerk": "کارمند", "translator": "مترجم", "accountant": "حسابدار"}
EMPLOYMENT_TYPE_MAP = {
    "FULL_TIME": "تمام وقت",
    "PART_TIME": "پاره وقت",
    "COMMISSION": "کمیسیون"
}
MARITAL_STATUS_MAP = {"Single": "مجرد", "Married": "متاهل"}


class UserManagementView(QWidget):
    add_employee_requested = Signal()
    edit_employee_requested = Signal(object)  # EmployeeFullData
    delete_employee_requested = Signal(str, str)
    search_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.apply_styles()
        self.connect_signals()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header section
        header_layout = QHBoxLayout()

        # Title
        # title_label = QLabel("مدیریت کارمندان")
        # title_font = QFont()
        # title_font.setPointSize(16)
        # title_font.setBold(True)
        # title_label.setFont(title_font)
        # header_layout.addWidget(title_label)

        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Search and action bar
        action_layout = QHBoxLayout()

        # Search box
        search_container = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("جستجو بر اساس نام، کد ملی یا شماره تماس...")
        self.search_input.setMinimumWidth(300)
        search_icon = qta.icon('fa5s.search')
        self.search_btn = QPushButton(icon=search_icon)
        self.search_btn.setFixedSize(36, 36)
        search_container.addWidget(self.search_input)
        search_container.addWidget(self.search_btn)
        action_layout.addLayout(search_container)

        action_layout.addStretch()

        # Add employee button
        self.add_employee_btn = QPushButton(" کارمند جدید")
        self.add_employee_btn.setIcon(qta.icon('fa5s.user-plus'))
        self.add_employee_btn.setMinimumHeight(36)
        action_layout.addWidget(self.add_employee_btn)

        main_layout.addLayout(action_layout)

        # Employee table
        self.employee_table = QTableWidget()
        self.employee_table.setColumnCount(6)
        self.employee_table.setHorizontalHeaderLabels([
            "نام کامل", "کد ملی", "شماره تماس", "تاریخ استخدام", "نوع قرارداد", "عملیات"
        ])

        # Configure table
        self.employee_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.employee_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.employee_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.employee_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.employee_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.employee_table.setAlternatingRowColors(True)
        self.employee_table.verticalHeader().setVisible(False)

        main_layout.addWidget(self.employee_table)

        # Status bar
        self.status_label = QLabel("آماده")
        self.status_label.setStyleSheet("color: #666; padding: 5px;")
        main_layout.addWidget(self.status_label)

    def apply_styles(self):
        """Apply modern styling to the view"""
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                font-family: 'Segoe UI', Tahoma, sans-serif;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QLineEdit {
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                gridline-color: #f0f0f0;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #E3F2FD;
                color: #000;
            }
            QHeaderView::section {
                background-color: #fafafa;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #e0e0e0;
                font-weight: bold;
                font-size: 13px;
            }
        """)

    def connect_signals(self):
        """Connect button clicks to signals"""
        self.add_employee_btn.clicked.connect(self._on_add_employee_clicked)
        self.search_btn.clicked.connect(self._on_search_clicked)
        self.search_input.returnPressed.connect(self._on_search_clicked)

    def populate_employee_table(self, employees: list):
        """Populate table with employee data"""
        self.employee_table.clearContents()
        self.employee_table.setRowCount(len(employees))

        for row, emp_data in enumerate(employees):
            # Full name
            full_name = f"{emp_data.first_name} {emp_data.last_name}"
            self.employee_table.setItem(row, 0, QTableWidgetItem(full_name))

            # National ID - convert to Persian numbers
            national_id_item = QTableWidgetItem(self.to_persian_numbers(emp_data.national_id))
            national_id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.employee_table.setItem(row, 1, national_id_item)

            # Phone
            phone_item = QTableWidgetItem(self.to_persian_numbers(emp_data.phone_number or "-"))
            phone_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.employee_table.setItem(row, 2, phone_item)

            # Hire date
            hire_date_str = self.to_persian_jalali_string(emp_data.hire_date) if emp_data.hire_date else "-"
            date_item = QTableWidgetItem(hire_date_str)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.employee_table.setItem(row, 3, date_item)

            # Employment type
            contract_type_fa = EMPLOYMENT_TYPE_MAP.get(emp_data.employment_type, emp_data.employment_type)
            contract_item = QTableWidgetItem(contract_type_fa)
            contract_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.employee_table.setItem(row, 4, contract_item)

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)

            edit_btn = QPushButton(icon=qta.icon('fa5s.edit', color='#4CAF50'))
            edit_btn.setFixedSize(32, 32)
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #E8F5E9;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #C8E6C9;
                }
            """)
            edit_btn.setToolTip("ویرایش کارمند")

            delete_btn = QPushButton(icon=qta.icon('fa5s.trash-alt', color='#F44336'))
            delete_btn.setFixedSize(32, 32)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFEBEE;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #FFCDD2;
                }
            """)
            delete_btn.setToolTip("حذف کارمند")

            edit_btn.clicked.connect(lambda chk, e=emp_data: self.edit_employee_requested.emit(e))
            delete_btn.clicked.connect(lambda chk, e=emp_data: self._confirm_delete(e))

            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            self.employee_table.setCellWidget(row, 5, actions_widget)

        # Update status
        self.status_label.setText(f"تعداد کارمندان: {len(employees)}")

    def _confirm_delete(self, emp_data):
        """Show confirmation dialog before deleting"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("تأیید حذف")
        msg_box.setText(f"آیا از حذف کارمند '{emp_data.first_name} {emp_data.last_name}' اطمینان دارید؟")
        msg_box.setInformativeText("این عملیات قابل بازگشت نیست.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

        yes_btn = msg_box.button(QMessageBox.StandardButton.Yes)
        yes_btn.setText("بله، حذف شود")
        no_btn = msg_box.button(QMessageBox.StandardButton.No)
        no_btn.setText("انصراف")

        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            self.delete_employee_requested.emit(emp_data.employee_id, emp_data.national_id)

    def _on_add_employee_clicked(self):
        """Emit signal to add new employee"""
        self.add_employee_requested.emit()

    def _on_search_clicked(self):
        """Emit search signal with query"""
        query = self.search_input.text().strip()
        self.search_requested.emit(query)

    @staticmethod
    def to_persian_numbers(text: str) -> str:
        """Convert English numbers to Persian"""
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        english_digits = '0123456789'
        trans_table = str.maketrans(english_digits, persian_digits)
        return str(text).translate(trans_table)

    @staticmethod
    def to_persian_jalali_string(date) -> str:
        """Convert date to Persian Jalali string - implement your conversion"""
        # Placeholder - implement with your Jalali conversion library
        if isinstance(date, datetime):
            return date.strftime('%Y/%m/%d')
        return str(date)


class EmployeeFormDialog(QDialog):
    """Dialog for adding/editing employee with validation"""

    def __init__(self, parent=None, employee_data=None):
        super().__init__(parent)
        self.employee_data = employee_data
        self.setup_ui()
        self.apply_styles()

        if employee_data:
            self.load_employee_data()
            self.setWindowTitle("ویرایش کارمند")
        else:
            self.setWindowTitle("افزودن کارمند جدید")

    def setup_ui(self):
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)

        # First Name
        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("نام کارمند")
        form_layout.addRow("* نام:", self.first_name_input)

        # Last Name
        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("نام خانوادگی کارمند")
        form_layout.addRow("* نام خانوادگی:", self.last_name_input)

        # National ID
        self.national_id_input = QLineEdit()
        self.national_id_input.setPlaceholderText("1234567890")
        self.national_id_input.setMaxLength(10)
        form_layout.addRow("* کد ملی:", self.national_id_input)

        # Phone
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("09123456789")
        self.phone_input.setMaxLength(11)
        form_layout.addRow("* شماره تماس:", self.phone_input)

        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("example@email.com")
        form_layout.addRow("ایمیل:", self.email_input)

        # Employment Type
        self.employment_type_combo = QComboBox()
        for key, value in EMPLOYMENT_TYPE_MAP.items():
            self.employment_type_combo.addItem(value, key)
        form_layout.addRow("* نوع قرارداد:", self.employment_type_combo)

        # Marital Status
        self.marital_status_combo = QComboBox()
        for key, value in MARITAL_STATUS_MAP.items():
            self.marital_status_combo.addItem(value, key)
        form_layout.addRow("وضعیت تأهل:", self.marital_status_combo)

        # Hire Date
        self.hire_date_input = QDateEdit()
        self.hire_date_input.setCalendarPopup(True)
        self.hire_date_input.setDate(QDate.currentDate())
        form_layout.addRow("* تاریخ استخدام:", self.hire_date_input)

        # Salary
        self.salary_input = QLineEdit()
        self.salary_input.setPlaceholderText("0")
        form_layout.addRow("حقوق پایه:", self.salary_input)

        # Is Active
        self.is_active_checkbox = QCheckBox("کارمند فعال")
        self.is_active_checkbox.setChecked(True)
        form_layout.addRow("", self.is_active_checkbox)

        layout.addLayout(form_layout)

        # Error label
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #F44336; font-weight: bold;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_btn = QPushButton("ذخیره")
        self.save_btn.setIcon(qta.icon('fa5s.save'))
        self.save_btn.setMinimumWidth(100)

        self.cancel_btn = QPushButton("انصراف")
        self.cancel_btn.setIcon(qta.icon('fa5s.times'))
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)

        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        # Connect signals
        self.save_btn.clicked.connect(self.validate_and_accept)
        self.cancel_btn.clicked.connect(self.reject)

    def apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLineEdit, QComboBox, QDateEdit {
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
                min-height: 20px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
                border-color: #2196F3;
            }
            QLabel {
                font-size: 13px;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QCheckBox {
                font-size: 13px;
            }
        """)

    def validate_and_accept(self):
        """Validate all fields before accepting"""
        errors = []

        # Validate required fields
        fields = [
            (self.first_name_input.text(), "نام"),
            (self.last_name_input.text(), "نام خانوادگی"),
            (self.national_id_input.text(), "کد ملی"),
            (self.phone_input.text(), "شماره تماس"),
        ]

        for value, field_name in fields:
            is_valid, error = self.validator.validate_required(value, field_name)
            if not is_valid:
                errors.append(error)

        # Validate national ID
        is_valid, error = self.validator.validate_national_id(self.national_id_input.text())
        if not is_valid:
            errors.append(error)

        # Validate phone
        is_valid, error = self.validator.validate_phone(self.phone_input.text())
        if not is_valid:
            errors.append(error)

        # Validate email (if provided)
        email = self.email_input.text()
        if email:
            is_valid, error = self.validator.validate_email(email)
            if not is_valid:
                errors.append(error)

        # Validate salary (if provided)
        salary = self.salary_input.text()
        if salary:
            is_valid, error = self.validator.validate_salary(salary)
            if not is_valid:
                errors.append(error)

        # Show errors or accept
        if errors:
            self.error_label.setText("\n".join(f"• {err}" for err in errors))
            self.error_label.show()
        else:
            self.error_label.hide()
            self.accept()

    def load_employee_data(self):
        """Load existing employee data into form"""
        if not self.employee_data:
            return

        self.first_name_input.setText(self.employee_data.first_name)
        self.last_name_input.setText(self.employee_data.last_name)
        self.national_id_input.setText(self.employee_data.national_id)
        self.phone_input.setText(self.employee_data.phone_number or "")
        self.email_input.setText(self.employee_data.email or "")
        self.salary_input.setText(str(self.employee_data.base_salary or ""))

        # Set combobox values
        emp_type_index = self.employment_type_combo.findData(self.employee_data.employment_type)
        if emp_type_index >= 0:
            self.employment_type_combo.setCurrentIndex(emp_type_index)

        # Set hire date
        if self.employee_data.hire_date:
            if isinstance(self.employee_data.hire_date, datetime):
                q_date = QDate(
                    self.employee_data.hire_date.year,
                    self.employee_data.hire_date.month,
                    self.employee_data.hire_date.day
                )
                self.hire_date_input.setDate(q_date)

    def get_form_data(self):
        """Get validated form data"""
        return {
            'first_name': self.first_name_input.text().strip(),
            'last_name': self.last_name_input.text().strip(),
            'national_id': self.national_id_input.text().strip(),
            'phone': self.phone_input.text().strip(),
            'email': self.email_input.text().strip() or None,
            'employment_type': self.employment_type_combo.currentData(),
            'marital_status': self.marital_status_combo.currentData(),
            'hire_date': self.hire_date_input.date().toPython(),
            'base_salary': float(self.salary_input.text().replace(',', '')) if self.salary_input.text() else None,
            'is_active': self.is_active_checkbox.isChecked()
        }
