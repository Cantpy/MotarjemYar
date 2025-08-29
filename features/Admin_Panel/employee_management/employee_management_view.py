# motarjemyar/employee_management/employee_management_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
                               QTableWidget, QDialog, QTabWidget, QFormLayout, QLineEdit,
                               QComboBox, QCheckBox, QDialogButtonBox, QSpinBox, QDoubleSpinBox,
                               QHeaderView, QTableWidgetItem)
from PySide6.QtCore import Qt, Signal, QDate
import qtawesome as qta
from shared.fonts.font_manager import FontManager
from features.Admin_Panel.employee_management.employee_management_models import EmployeeFullData
from shared.widgets.persian_calendar import BirthdayPicker, DataDatePicker
from shared.utils.persian_tools import to_persian_jalali_string, to_persian_numbers
from decimal import Decimal


ROLE_MAP = {"admin": "مدیر", "clerk": "کارمند", "translator": "مترجم", "accountant": "حسابدار"}
PAYMENT_TYPE_MAP = {"Full-time": "تمام وقت", "Part-time": "پاره وقت", "Commission": "کمیسیون"}
MARITAL_STATUS_MAP = {"Single": "مجرد", "Married": "متاهل"}


class UserEditDialog(QDialog):
    """A dialog for both creating and editing employee and their payroll info."""

    def __init__(self, employee_data: EmployeeFullData | None = None, parent=None):
        super().__init__(parent)
        self.is_edit_mode = employee_data is not None
        self.employee_id = employee_data.employee_id if self.is_edit_mode else None

        self.setWindowTitle("ویرایش کارمند" if self.is_edit_mode else "ایجاد کارمند جدید")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumWidth(550)
        self.setFont(FontManager.get_font(size=11))

        main_layout = QVBoxLayout(self)

        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # --- Create and Add THREE Tabs ---
        personal_info_widget = self._create_personal_info_tab()
        login_info_widget = self._create_login_info_tab()
        payroll_info_widget = self._create_payroll_info_tab()

        tab_widget.addTab(personal_info_widget, "اطلاعات شخصی")
        tab_widget.addTab(login_info_widget, "اطلاعات ورود به سیستم")
        tab_widget.addTab(payroll_info_widget, "اطلاعات قرارداد و حقوق")

        # --- Dialog Buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        if self.is_edit_mode:
            self.set_data(employee_data)

        # Set initial visibility of salary/commission fields
        self._on_payment_type_changed()

    def _create_personal_info_tab(self):
        widget = QWidget()
        form_layout = QFormLayout(widget)
        self.first_name_edit = QLineEdit()
        self.last_name_edit = QLineEdit()
        self.national_id_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.dob_edit = BirthdayPicker()
        self.hire_date_edit = DataDatePicker()

        form_layout.addRow("نام:", self.first_name_edit)
        form_layout.addRow("نام خانوادگی:", self.last_name_edit)
        form_layout.addRow("کد ملی:", self.national_id_edit)
        form_layout.addRow("ایمیل:", self.email_edit)
        form_layout.addRow("تلفن:", self.phone_edit)
        form_layout.addRow("تاریخ تولد:", self.dob_edit)
        form_layout.addRow("تاریخ استخدام:", self.hire_date_edit)
        return widget

    def _create_login_info_tab(self):
        widget = QWidget()
        form_layout = QFormLayout(widget)
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit(echoMode=QLineEdit.Password)
        self.role_combo = QComboBox()
        self.role_combo.addItems(["clerk", "translator", "accountant", "admin"])
        self.is_active_check = QCheckBox("اکانت فعال است")

        if self.is_edit_mode:
            self.username_edit.setReadOnly(True)
            self.password_edit.setPlaceholderText("برای تغییر، رمز جدید را وارد کنید")

        form_layout.addRow("نام کاربری:", self.username_edit)
        form_layout.addRow("رمز عبور:", self.password_edit)
        form_layout.addRow("نقش سیستمی:", self.role_combo)
        form_layout.addRow("", self.is_active_check)
        return widget

    def _create_payroll_info_tab(self):
        widget = QWidget()
        form_layout = QFormLayout(widget)
        self.payment_type_combo = QComboBox()
        self.payment_type_combo.addItems(PAYMENT_TYPE_MAP.values())

        self.daily_payment_rials_spinbox = QSpinBox(maximum=100000000, singleStep=100000)
        self.commission_rate_spinbox = QDoubleSpinBox(maximum=1.0, singleStep=0.01, decimals=2)

        self.marital_status_combo = QComboBox()
        self.marital_status_combo.addItems(MARITAL_STATUS_MAP.values())
        self.children_spinbox = QSpinBox(maximum=10)

        form_layout.addRow("نوع قرارداد:", self.payment_type_combo)
        form_layout.addRow("دستمزد روزانه (ریال):", self.daily_payment_rials_spinbox)
        form_layout.addRow("درصد کمیسیون (مثال: 0.25):", self.commission_rate_spinbox)
        form_layout.addRow("وضعیت تاهل:", self.marital_status_combo)
        form_layout.addRow("تعداد فرزندان:", self.children_spinbox)

        self.payment_type_combo.currentTextChanged.connect(self._on_payment_type_changed)
        return widget

    def _on_payment_type_changed(self):
        selected_text = self.payment_type_combo.currentText()
        is_commission = selected_text == PAYMENT_TYPE_MAP["Commission"]

        self.daily_payment_rials_spinbox.setVisible(not is_commission)
        self.commission_rate_spinbox.setVisible(is_commission)

    def set_data(self, data: EmployeeFullData):
        """Populates the dialog fields with data for editing."""
        # Populate Personal Info Tab
        self.first_name_edit.setText(data.first_name)
        self.last_name_edit.setText(data.last_name)
        self.national_id_edit.setText(data.national_id)
        self.email_edit.setText(data.email)
        self.phone_edit.setText(data.phone_number)

        if data.date_of_birth:
            self.dob_edit.set_date(QDate(data.date_of_birth.year, data.date_of_birth.month, data.date_of_birth.day))
        if data.hire_date:
            self.hire_date_edit.set_date(QDate(data.hire_date.year, data.hire_date.month, data.hire_date.day))

        # Populate Login Info Tab
        self.username_edit.setText(data.username)
        self.role_combo.setCurrentText(data.role)
        self.is_active_check.setChecked(data.is_active)

        # Populate Payroll Info Tab
        self.payment_type_combo.setCurrentText(PAYMENT_TYPE_MAP.get(data.payment_type, ""))
        self.daily_payment_rials_spinbox.setValue(int(data.custom_daily_payment_rials or 0))
        self.commission_rate_spinbox.setValue(float(data.commission_rate or 0.0))
        self.marital_status_combo.setCurrentText(MARITAL_STATUS_MAP.get(data.marital_status, ""))
        self.children_spinbox.setValue(data.children_count)

    def get_data(self) -> EmployeeFullData:
        """Collects data from fields, mapping display values back to storage values."""

        def get_key_from_value(d, val):
            return next((k for k, v in d.items() if v == val), None)

        return EmployeeFullData(
            employee_id=getattr(self, 'employee_id', None),
            user_id=getattr(self, 'user_id', None),
            first_name=self.first_name_edit.text(),
            last_name=self.last_name_edit.text(),
            national_id=self.national_id_edit.text(),
            email=self.email_edit.text(),
            phone_number=self.phone_edit.text(),
            date_of_birth=self.dob_edit.get_date(),
            hire_date=self.hire_date_edit.get_date(),
            # Login Info
            username=self.username_edit.text(),
            password=self.password_edit.text(),
            role=self.role_combo.currentText(),
            is_active=self.is_active_check.isChecked(),
            # Payroll Info
            payment_type=get_key_from_value(PAYMENT_TYPE_MAP, self.payment_type_combo.currentText()),
            custom_daily_payment_rials=Decimal(self.daily_payment_rials_spinbox.value()),
            commission_rate=Decimal(self.commission_rate_spinbox.value()),
            marital_status=get_key_from_value(MARITAL_STATUS_MAP, self.marital_status_combo.currentText()),
            children_count=self.children_spinbox.value()
        )


class UserManagementView(QWidget):
    add_employee_requested = Signal()
    edit_employee_requested = Signal(EmployeeFullData)
    delete_employee_requested = Signal(str)  # Emits employee_id

    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        action_layout = QHBoxLayout()
        self.add_employee_btn = QPushButton(" کارمند جدید", icon=qta.icon('fa5s.user-plus'))
        action_layout.addWidget(self.add_employee_btn)
        action_layout.addStretch()
        main_layout.addLayout(action_layout)

        self.employee_table = QTableWidget()
        self.employee_table.setColumnCount(5)
        self.employee_table.setHorizontalHeaderLabels(["نام کامل", "کد ملی", "تاریخ استخدام", "نوع قرارداد", ""])
        self.employee_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.employee_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.employee_table.setEditTriggers(QTableWidget.NoEditTriggers)
        main_layout.addWidget(self.employee_table)

        self.add_employee_btn.clicked.connect(self.add_employee_requested)

    def populate_employee_table(self, employees: list[EmployeeFullData]):
        self.employee_table.clearContents()
        self.employee_table.setRowCount(len(employees))
        for row, emp_data in enumerate(employees):
            full_name = f"{emp_data.first_name} {emp_data.last_name}"
            hire_date_str = to_persian_jalali_string(emp_data.hire_date) if emp_data.hire_date else "-"
            contract_type_fa = PAYMENT_TYPE_MAP.get(emp_data.payment_type, emp_data.payment_type)

            self.employee_table.setItem(row, 0, QTableWidgetItem(full_name))
            self.employee_table.setItem(row, 1, QTableWidgetItem(to_persian_numbers(emp_data.national_id)))
            self.employee_table.setItem(row, 2, QTableWidgetItem(hire_date_str))
            self.employee_table.setItem(row, 3, QTableWidgetItem(contract_type_fa))

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            edit_btn = QPushButton(icon=qta.icon('fa5s.edit'))
            delete_btn = QPushButton(icon=qta.icon('fa5s.trash-alt'))
            edit_btn.clicked.connect(lambda chk, e=emp_data: self.edit_employee_requested.emit(e))
            delete_btn.clicked.connect(lambda chk, e_id=emp_data.employee_id: self.delete_employee_requested.emit(e_id))
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            self.employee_table.setCellWidget(row, 4, actions_widget)
