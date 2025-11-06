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
    view_employee_details_requested = Signal(str) # Emits employee_id
    search_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.employee_data_map = {}  # Maps employee_id to EmployeeFullData
        self.setup_ui()
        self.apply_styles()
        self.connect_signals()

    def setup_ui(self):
        """Setup the main UI components"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        action_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("جستجو بر اساس نام، کد ملی یا شماره تماس...")
        self.search_input.setMinimumWidth(300)
        search_icon = qta.icon('fa5s.search')
        self.search_btn = QPushButton(icon=search_icon)
        self.search_btn.setFixedSize(36, 36)
        action_layout.addWidget(self.search_input)
        action_layout.addWidget(self.search_btn)
        action_layout.addStretch()
        self.add_employee_btn = QPushButton(" کارمند جدید")
        self.add_employee_btn.setIcon(qta.icon('fa5s.user-plus'))
        self.add_employee_btn.setMinimumHeight(36)
        action_layout.addWidget(self.add_employee_btn)
        main_layout.addLayout(action_layout)

        self.employee_table = QTableWidget()
        self.employee_table.setColumnCount(8)
        self.employee_table.setHorizontalHeaderLabels([
            "نام کامل", "کد ملی", "شماره بیمه", "سمت", "شماره تماس", "تاریخ استخدام", "نوع قرارداد", "عملیات"
        ])
        self.employee_table.setToolTip("برای مشاهده جزئیات کامل و تاریخچه تغییرات، روی یک ردیف دوبار کلیک کنید.")

        header = self.employee_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.employee_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.employee_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.employee_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.employee_table.setAlternatingRowColors(True)
        self.employee_table.verticalHeader().setVisible(False)
        main_layout.addWidget(self.employee_table)

        self.status_label = QLabel("آماده")
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
        self.add_employee_btn.clicked.connect(self.add_employee_requested.emit)
        self.search_btn.clicked.connect(self._on_search_clicked)
        self.search_input.returnPressed.connect(self._on_search_clicked)
        self.employee_table.itemDoubleClicked.connect(self._on_item_double_clicked)

    def populate_employee_table(self, employees: list):
        """Populate the employee table with data."""
        self.employee_table.clearContents()
        self.employee_table.setRowCount(len(employees))
        self.employee_data_map.clear()

        for row, emp_data in enumerate(employees):
            self.employee_data_map[row] = emp_data  # Store data for signal emission

            # Col 0: Full Name
            self.employee_table.setItem(row, 0, QTableWidgetItem(f"{emp_data.first_name} {emp_data.last_name}"))

            # Col 1: National ID
            self.employee_table.setItem(row, 1, QTableWidgetItem(self.to_persian_numbers(emp_data.national_id)))

            # Col 2: Insurance Number
            self.employee_table.setItem(row, 2,
                                        QTableWidgetItem(self.to_persian_numbers(emp_data.insurance_number or "-")))

            # Col 3: Role
            self.employee_table.setItem(row, 3, QTableWidgetItem(emp_data.role_name_fa))

            # Col 4: Phone Number
            self.employee_table.setItem(row, 4, QTableWidgetItem(self.to_persian_numbers(emp_data.phone_number or "-")))

            # Col 5: Hire Date
            hire_date_str = self.to_persian_jalali_string(emp_data.hire_date) if emp_data.hire_date else "-"
            self.employee_table.setItem(row, 5, QTableWidgetItem(hire_date_str))

            # Col 6: Employment Type
            contract_type_fa = EMPLOYMENT_TYPE_MAP.get(
                emp_data.employment_type,
                getattr(emp_data.employment_type, "value", str(emp_data.employment_type))
            )
            self.employee_table.setItem(row, 6, QTableWidgetItem(str(contract_type_fa)))

            # Col 7: Actions
            self._create_action_buttons(row, emp_data)

        self.status_label.setText(f"تعداد کارمندان: {len(employees)}")

    def _create_action_buttons(self, row, emp_data):
        """Create Edit and Delete buttons for each row"""
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(4, 4, 4, 4)
        actions_layout.setSpacing(4)

        edit_btn = QPushButton(icon=qta.icon('fa5s.edit', color='#4CAF50'))
        edit_btn.setToolTip("ویرایش کارمند")
        delete_btn = QPushButton(icon=qta.icon('fa5s.trash-alt', color='#F44336'))
        delete_btn.setToolTip("حذف کارمند")

        for btn in [edit_btn, delete_btn]:
            btn.setFixedSize(32, 32)
            btn.setStyleSheet("background-color: transparent; border: none;")

        edit_btn.clicked.connect(lambda chk, e=emp_data: self.edit_employee_requested.emit(e))
        delete_btn.clicked.connect(lambda chk, e=emp_data: self._confirm_delete(e))

        actions_layout.addWidget(edit_btn)
        actions_layout.addWidget(delete_btn)
        self.employee_table.setCellWidget(row, 7, actions_widget)

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

    def _on_item_double_clicked(self, item: QTableWidgetItem):
        """Handle double-click to view employee details"""
        row = item.row()
        if row in self.employee_data_map:
            employee_data = self.employee_data_map[row]
            self.view_employee_details_requested.emit(employee_data.employee_id)

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
