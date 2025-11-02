# features/Admin_Panel/wage_calculator_preview/wage_calculator_preview_view.py

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QGroupBox, QFrame, QFormLayout,
                               QSpinBox, QComboBox, QStackedWidget, QWidget)
from PySide6.QtCore import Signal
import qtawesome as qta
from shared.widgets.persian_calendar import DataDatePicker
# --- FIX: Import widget from its new local path ---
from features.Admin_Panel.wage_calculator_preview.salary_slip_viewer import SalarySlipViewer
# --- FIX: Explicitly import from the core wage_calculator package ---
from features.Admin_Panel.wage_calculator.wage_calculator_models import EmployeeInfo, PayslipData
from shared import show_warning_message_box


class WageCalculatorPreviewDialog(QDialog):
    generate_requested = Signal(dict)
    print_requested = Signal()
    save_as_requested = Signal()

    def __init__(self, employees: list[EmployeeInfo], parent=None):
        super().__init__(parent)
        self.setWindowTitle("ایجاد فیش حقوقی جدید")
        self.setMinimumSize(1024, 650)

        main_layout = QHBoxLayout(self)

        # --- Left Side: Control Panel ---
        self.control_panel = self._create_control_panel()
        main_layout.addWidget(self.control_panel)

        # --- Right Side: Content Area (Input/Preview) ---
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget, 1)

        # --- Page 1: Input Form ---
        self.input_page = self._create_input_page(employees)
        self.stacked_widget.addWidget(self.input_page)

        # --- Page 2: Payslip Preview ---
        self.payslip_preview = SalarySlipViewer()
        self.stacked_widget.addWidget(self.payslip_preview)

    def _create_control_panel(self) -> QFrame:
        panel = QFrame()
        panel.setFixedWidth(280)
        layout = QVBoxLayout(panel)

        self.generate_btn = QPushButton(" ایجاد و پیش‌نمایش")
        self.generate_btn.setIcon(qta.icon('fa5s.cogs'))
        self.generate_btn.clicked.connect(self._on_generate_clicked)
        layout.addWidget(self.generate_btn)

        layout.addStretch(1)

        self.print_btn = QPushButton(" چاپ")
        self.print_btn.setIcon(qta.icon('fa5s.print'))
        self.print_btn.clicked.connect(self.print_requested)
        layout.addWidget(self.print_btn)

        self.save_as_btn = QPushButton(" ذخیره فایل...")
        self.save_as_btn.setIcon(qta.icon('fa5s.save'))
        self.save_as_btn.clicked.connect(self.save_as_requested)
        layout.addWidget(self.save_as_btn)

        layout.addStretch(2)

        self.confirm_save_btn = QPushButton(" تایید و ذخیره نهایی")
        self.confirm_save_btn.setIcon(qta.icon('fa5s.check-circle'))
        self.confirm_save_btn.setStyleSheet("background-color: #28a745;")
        self.confirm_save_btn.clicked.connect(self.accept)  # Triggers the accepted signal
        layout.addWidget(self.confirm_save_btn)

        # Set initial visibility
        self.print_btn.setVisible(False)
        self.save_as_btn.setVisible(False)
        self.confirm_save_btn.setVisible(False)

        return panel

    def _create_input_page(self, employees: list[EmployeeInfo]) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 0, 10, 0)

        group = QGroupBox("اطلاعات دوره محاسبه")
        form = QFormLayout(group)
        form.setSpacing(15)

        self.employee_combo = QComboBox()
        for emp in employees:
            self.employee_combo.addItem(emp.full_name, emp.employee_id)

        self.start_date_input = DataDatePicker()
        self.end_date_input = DataDatePicker()
        self.overtime_input = QSpinBox()
        self.overtime_input.setMaximum(200)

        form.addRow("انتخاب کارمند:", self.employee_combo)
        form.addRow("از تاریخ:", self.start_date_input)
        form.addRow("تا تاریخ:", self.end_date_input)
        form.addRow("ساعات اضافه کار:", self.overtime_input)

        layout.addWidget(group)
        layout.addStretch()
        return page

    def _on_generate_clicked(self):
        if not self.start_date_input.get_date() or not self.end_date_input.get_date():
            show_warning_message_box(self, "خطا", "لطفا بازه زمانی را به طور کامل مشخص کنید.")
            return

        if self.start_date_input.get_date() > self.end_date_input.get_date():
            show_warning_message_box(self, "خطا", "تاریخ شروع نمی‌تواند بعد از تاریخ پایان باشد.")
            return

        inputs = {
            'employee_id': self.employee_combo.currentData(),
            'start_date': self.start_date_input.get_date(),
            'end_date': self.end_date_input.get_date(),
            'overtime_hours': self.overtime_input.value()
        }
        self.generate_requested.emit(inputs)

    def show_preview(self, payslip_data: PayslipData):
        """Switches to the preview page, populates it, and updates button visibility."""
        self.payslip_preview.populate(payslip_data)
        self.stacked_widget.setCurrentWidget(self.payslip_preview)

        self.setWindowTitle(f"پیش‌نمایش فیش حقوقی: {payslip_data.employee_name}")
        self.generate_btn.setVisible(False)
        self.print_btn.setVisible(True)
        self.save_as_btn.setVisible(True)
        self.confirm_save_btn.setVisible(True)
