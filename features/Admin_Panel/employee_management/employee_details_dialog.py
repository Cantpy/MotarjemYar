# features/Admin_Panel/employee_management/employee_details_dialog.py

import qtawesome as qta
import jdatetime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
                               QPushButton, QTabWidget, QWidget, QLabel, QFrame, QTableWidget,
                               QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from features.Admin_Panel.employee_management.employee_management_models import EmployeeFullData

# Re-use maps from other files for consistency
EMPLOYMENT_TYPE_MAP = {"full_time": "تمام وقت", "part_time": "پاره وقت", "commission": "کمیسیون"}
MARITAL_STATUS_MAP = {"Single": "مجرد", "Married": "متاهل"}


class EmployeeDetailsDialog(QDialog):
    def __init__(self, data: EmployeeFullData, parent=None):
        super().__init__(parent)
        self.employee_data = data
        self.setWindowTitle(f"جزئیات کارمند: {data.first_name} {data.last_name}")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumWidth(700)
        self.setMinimumHeight(550)

        self.setup_ui()
        self.populate_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)

        self.tab_widget = QTabWidget()
        details_tab = self._create_details_tab()
        history_tab = self._create_history_tab()

        self.tab_widget.addTab(details_tab, qta.icon('fa5s.id-card'), " اطلاعات کامل")
        self.tab_widget.addTab(history_tab, qta.icon('fa5s.history'), " تاریخچه تغییرات")
        main_layout.addWidget(self.tab_widget)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.close_btn = QPushButton(" بستن")
        self.close_btn.setIcon(qta.icon('fa5s.times'))
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        main_layout.addLayout(button_layout)

    def _create_details_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(15)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.detail_fields = {}
        fields_to_create = [
            ("کد پرسنلی", "employee_code"), ("نام", "first_name"), ("نام خانوادگی", "last_name"),
            ("کد ملی", "national_id"), ("شماره بیمه", "insurance_number"), ("سمت", "role_name_fa"),
            ("شماره تماس", "phone_number"), ("ایمیل", "email"), ("تاریخ تولد", "date_of_birth"),
            ("تاریخ استخدام", "hire_date"), ("نوع قرارداد", "employment_type"), ("وضعیت تاهل", "marital_status"),
            ("تعداد فرزندان", "children_count"), ("حقوق پایه (ریال)", "base_salary_rials")
        ]

        for label, key in fields_to_create:
            field = QLineEdit()
            field.setReadOnly(True)
            field.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
            layout.addRow(f"{label}:", field)
            self.detail_fields[key] = field

        return widget

    def _create_history_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "تاریخ تغییر", "تغییر توسط", "فیلد", "مقدار قدیمی", "مقدار جدید"
        ])
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)

        layout.addWidget(self.history_table)
        return widget

    def populate_data(self):
        data = self.employee_data

        # Populate details tab
        for key, field in self.detail_fields.items():
            value = getattr(data, key)
            display_value = ""

            if value is None:
                display_value = "-"
            elif isinstance(value, jdatetime.date):
                display_value = value.strftime("%Y/%m/%d")
            elif key == "employment_type":
                display_value = EMPLOYMENT_TYPE_MAP.get(value, value)
            elif key == "marital_status":
                display_value = MARITAL_STATUS_MAP.get(value, value)
            elif key == "base_salary_rials":
                display_value = f"{int(value):,}"
            else:
                display_value = str(value)

            field.setText(display_value)

        # Populate history tab
        self.history_table.setRowCount(len(data.edit_logs))
        for row, log in enumerate(data.edit_logs):
            self.history_table.setItem(row, 0, QTableWidgetItem(log.edited_at.strftime("%Y-%m-%d %H:%M")))
            self.history_table.setItem(row, 1, QTableWidgetItem(log.edited_by or "سیستم"))
            self.history_table.setItem(row, 2, QTableWidgetItem(log.field_name))
            self.history_table.setItem(row, 3, QTableWidgetItem(log.old_value or "-"))
            self.history_table.setItem(row, 4, QTableWidgetItem(log.new_value or "-"))
