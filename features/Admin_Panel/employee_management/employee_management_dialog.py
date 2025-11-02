# features/Admin_Panel/employee_management/employee_management_dialog.py

import qtawesome as qta
from decimal import Decimal
import jdatetime

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox, QSpinBox,
                               QDoubleSpinBox, QPushButton, QTabWidget, QWidget, QLabel, QFrame)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from shared.orm_models.payroll_models import EmploymentType
from shared.widgets.persian_calendar import BirthdayPicker, DataDatePicker
from features.Admin_Panel.employee_management.employee_management_models import EmployeeFullData

ROLE_MAP = {"admin": "مدیر", "clerk": "کارمند", "translator": "مترجم", "accountant": "حسابدار"}
EMPLOYMENT_TYPE_MAP = {
    EmploymentType.FULL_TIME.name: "تمام وقت",
    EmploymentType.PART_TIME.name: "پاره وقت",
    EmploymentType.COMMISSION.name: "کمیسیون"
}
MARITAL_STATUS_MAP = {"Single": "مجرد", "Married": "متاهل"}


class EmployeeEditDialog(QDialog):
    """Dialog for creating and editing employee PAYROLL and PERSONAL data."""
    save_requested = Signal(object)

    def __init__(self, employee_data: EmployeeFullData | None = None, parent=None):
        super().__init__(parent)
        self.is_edit_mode = employee_data is not None and employee_data.employee_code

        if employee_data:
            self.employee_id = employee_data.employee_id
        else:
            self.employee_id = None

        self.setWindowTitle("ویرایش کارمند" if self.is_edit_mode else "ایجاد کارمند جدید")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumWidth(650)
        self.setMinimumHeight(500)

        self.setup_ui()
        self.connect_interactive_signals()

        if self.is_edit_mode and employee_data:
            self.set_data(employee_data)

        self._on_employment_type_changed()

    def setup_ui(self):
        """Setup the complete UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)

        # Header with icon and title
        header_layout = QHBoxLayout()
        icon_label = QLabel()
        icon = qta.icon('fa5s.user-edit', color='#2196F3') if self.is_edit_mode else qta.icon('fa5s.user-plus',
                                                                                              color='#4CAF50')
        icon_label.setPixmap(icon.pixmap(32, 32))

        title_label = QLabel("ویرایش اطلاعات کارمند" if self.is_edit_mode else "افزودن کارمند جدید")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)

        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)

        # Tab widget
        self.tab_widget = QTabWidget()
        personal_info_widget = self._create_personal_info_tab()
        payroll_info_widget = self._create_payroll_info_tab()
        self.tab_widget.addTab(personal_info_widget, qta.icon('fa5s.user'), " اطلاعات شخصی")
        self.tab_widget.addTab(payroll_info_widget, qta.icon('fa5s.money-bill-wave'), " اطلاعات قرارداد")
        main_layout.addWidget(self.tab_widget)

        # Error label to display validation messages
        self.error_label = QLabel()
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("""
                    QLabel {
                        background-color: #FFEBEE;
                        color: #C62828;
                        padding: 10px;
                        border-radius: 4px;
                        border-left: 4px solid #F44336;
                    }
                """)
        self.error_label.hide()  # Initially hidden
        main_layout.addWidget(self.error_label)

        # Button box
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.save_btn = QPushButton(" ذخیره")
        self.save_btn.setIcon(qta.icon('fa5s.save'))
        self.cancel_btn = QPushButton(" انصراف")
        self.cancel_btn.setIcon(qta.icon('fa5s.times'))
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(button_layout)

        self.cancel_btn.clicked.connect(self.reject)

    def connect_interactive_signals(self):
        """Connect signals for user interaction."""
        # Save button emits a signal instead of closing the dialog
        self.save_btn.clicked.connect(self._on_save_clicked)
        self.cancel_btn.clicked.connect(self.reject)

        # Hide error message when user starts typing again
        self.employee_code_edit.textChanged.connect(self.clear_error)
        self.first_name_edit.textChanged.connect(self.clear_error)
        self.last_name_edit.textChanged.connect(self.clear_error)
        self.national_id_edit.textChanged.connect(self.clear_error)
        self.phone_edit.textChanged.connect(self.clear_error)
        self.email_edit.textChanged.connect(self.clear_error)

    def _on_save_clicked(self):
        """Gathers data and emits the save_requested signal."""
        employee_data = self.get_data()
        self.save_requested.emit(employee_data)

    def show_error(self, message: str):
        """Makes the error label visible and sets its text."""
        self.error_label.setText(message)
        self.error_label.show()

    def clear_error(self):
        """Hides the error label."""
        self.error_label.hide()

    def _create_personal_info_tab(self):
        widget = QWidget()
        form_layout = QFormLayout(widget)
        form_layout.setSpacing(15)

        self.employee_code_edit = QLineEdit()
        self.employee_code_edit.setPlaceholderText("کد پرسنلی یکتا برای کارمند")
        if self.is_edit_mode:
            self.employee_code_edit.setReadOnly(True)
        self.first_name_edit = QLineEdit()
        self.first_name_edit.setPlaceholderText("نام کوچک کارمند")
        self.last_name_edit = QLineEdit()
        self.last_name_edit.setPlaceholderText("نام خانوادگی کارمند")
        self.national_id_edit = QLineEdit()
        self.national_id_edit.setPlaceholderText("کد ملی 10 رقمی")
        self.national_id_edit.setMaxLength(10)
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("آدرس ایمیل (اختیاری)")
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("شماره تلفن همراه 11 رقمی")
        self.phone_edit.setMaxLength(11)
        self.dob_edit = BirthdayPicker(self)
        self.hire_date_edit = DataDatePicker(self)

        form_layout.addRow("* کد پرسنلی:", self.employee_code_edit)
        form_layout.addRow("* نام:", self.first_name_edit)
        form_layout.addRow("* نام خانوادگی:", self.last_name_edit)
        form_layout.addRow("* کد ملی:", self.national_id_edit)
        form_layout.addRow("* تلفن:", self.phone_edit)
        form_layout.addRow("ایمیل:", self.email_edit)
        form_layout.addRow("تاریخ تولد:", self.dob_edit)
        form_layout.addRow("* تاریخ استخدام:", self.hire_date_edit)
        return widget

    def _create_payroll_info_tab(self):
        widget = QWidget()
        form_layout = QFormLayout(widget)
        form_layout.setSpacing(15)

        self.employment_type_combo = QComboBox()
        for key, value in EMPLOYMENT_TYPE_MAP.items():
            self.employment_type_combo.addItem(value, key)
        self.employment_type_combo.currentIndexChanged.connect(self._on_employment_type_changed)
        form_layout.addRow("* نوع قرارداد:", self.employment_type_combo)

        self.daily_payment_rials_spinbox = QSpinBox()
        self.daily_payment_rials_spinbox.setRange(0, 999999999)
        self.daily_payment_rials_spinbox.setSingleStep(100000)
        self.daily_payment_rials_spinbox.setGroupSeparatorShown(True)
        self.daily_payment_label = QLabel("* دستمزد روزانه (ریال):")
        form_layout.addRow(self.daily_payment_label, self.daily_payment_rials_spinbox)

        self.commission_rate_spinbox = QDoubleSpinBox()
        self.commission_rate_spinbox.setRange(0.0, 1.0)
        self.commission_rate_spinbox.setSingleStep(0.01)
        self.commission_rate_spinbox.setDecimals(2)
        self.commission_rate_label = QLabel("* درصد کمیسیون (مثال: 0.25):")
        form_layout.addRow(self.commission_rate_label, self.commission_rate_spinbox)

        self.marital_status_combo = QComboBox()
        for key, value in MARITAL_STATUS_MAP.items():
            self.marital_status_combo.addItem(value, key)
        form_layout.addRow("وضعیت تأهل:", self.marital_status_combo)

        self.children_spinbox = QSpinBox()
        self.children_spinbox.setRange(0, 20)
        form_layout.addRow("تعداد فرزندان:", self.children_spinbox)
        return widget

    def _on_employment_type_changed(self):
        is_commission = self.employment_type_combo.currentData() == "COMMISSION"
        self.daily_payment_label.setVisible(not is_commission)
        self.daily_payment_rials_spinbox.setVisible(not is_commission)
        self.commission_rate_label.setVisible(is_commission)
        self.commission_rate_spinbox.setVisible(is_commission)

    def set_data(self, data: EmployeeFullData):
        """Populate the dialog fields with existing employee data."""
        self.employee_code_edit.setText(data.employee_code or "")
        self.first_name_edit.setText(data.first_name or "")
        self.last_name_edit.setText(data.last_name or "")
        self.national_id_edit.setText(data.national_id or "")
        self.email_edit.setText(data.email or "")
        self.phone_edit.setText(data.phone_number or "")

        # CORRECTED: Convert Gregorian date to Jalali and use the custom set_date method
        if data.date_of_birth:
            jalali_dob = jdatetime.date.fromgregorian(date=data.date_of_birth)
            self.dob_edit.set_date(jalali_dob)

        if data.hire_date:
            jalali_hire_date = jdatetime.date.fromgregorian(date=data.hire_date)
            self.hire_date_edit.set_date(jalali_hire_date)

        emp_type_index = self.employment_type_combo.findData(data.employment_type)
        if emp_type_index >= 0: self.employment_type_combo.setCurrentIndex(emp_type_index)

        self.daily_payment_rials_spinbox.setValue(int(data.base_salary_rials or 0))
        self.commission_rate_spinbox.setValue(float(data.commission_rate_pct or 0))

        marital_index = self.marital_status_combo.findData(data.marital_status)
        if marital_index >= 0: self.marital_status_combo.setCurrentIndex(marital_index)

        self.children_spinbox.setValue(data.children_count or 0)

    def get_data(self) -> EmployeeFullData:
        """Collect and return data from all form fields as a DTO."""
        return EmployeeFullData(
            employee_id=self.employee_id,
            employee_code=self.employee_code_edit.text().strip(),
            first_name=self.first_name_edit.text().strip(),
            last_name=self.last_name_edit.text().strip(),
            national_id=self.national_id_edit.text().strip(),
            email=self.email_edit.text().strip() or None,
            phone_number=self.phone_edit.text().strip(),
            date_of_birth=self.dob_edit.get_date(),
            hire_date=self.hire_date_edit.get_date(),
            employment_type=self.employment_type_combo.currentData(),
            base_salary_rials=Decimal(self.daily_payment_rials_spinbox.value()),
            commission_rate_pct=Decimal(str(self.commission_rate_spinbox.value())),
            marital_status=self.marital_status_combo.currentData(),
            children_count=self.children_spinbox.value()
        )
