# motarjemyar/wage_calculator_preview/wage_calculator_preview_view.py

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QGroupBox, QFrame, QFormLayout,
                               QSpinBox, QComboBox, QStackedWidget, QWidget, QLabel)
from PySide6.QtCore import Qt, Signal
import qtawesome as qta
from shared.widgets.persian_calendar import DataDatePicker, BirthdayPicker
from shared.fonts.font_manager import FontManager
from shared.utils.persian_tools import to_persian_numbers
from features.Admin_Panel.wage_calculator_preview.payslip_widget import PayslipWidget
from features.Admin_Panel.wage_calculator.wage_calculator_models import EmployeeInfo, PayslipData
from shared import show_warning_message_box


class WageCalculatorPreviewDialog(QDialog):
    generate_requested = Signal(dict)
    print_requested = Signal()
    share_requested = Signal()

    def __init__(self, employees: list[EmployeeInfo], parent=None):
        super().__init__(parent)
        self.setWindowTitle("ایجاد فیش حقوقی جدید")
        self.setMinimumSize(1150, 700)

        main_layout = QHBoxLayout(self)

        # --- Left Side: Control Panel ---
        control_panel = QFrame()
        control_panel.setFixedWidth(320)
        control_layout = QVBoxLayout(control_panel)
        main_layout.addWidget(control_panel)

        # --- Right Side: Content Area (Input/Preview) ---
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget, 1)

        # --- Page 1: Input Form ---
        self.input_page = self._create_input_page(employees)
        self.stacked_widget.addWidget(self.input_page)

        # --- Page 2: Payslip Preview ---
        self.payslip_preview = PayslipWidget()
        self.stacked_widget.addWidget(self.payslip_preview)

        # --- Control Panel Buttons ---
        self.generate_btn = QPushButton(" ایجاد و پیش‌نمایش", icon=qta.icon('fa5s.cogs'))
        self.print_btn = QPushButton(" چاپ", icon=qta.icon('fa5s.print'))
        self.share_btn = QPushButton(" اشتراک گذاری", icon=qta.icon('fa5s.share-alt'))
        self.print_btn.setVisible(False)
        self.share_btn.setVisible(False)

        control_layout.addWidget(self.generate_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.print_btn)
        control_layout.addWidget(self.share_btn)

        self.generate_btn.clicked.connect(self._on_generate_clicked)
        self.print_btn.clicked.connect(self.print_requested)
        self.share_btn.clicked.connect(self.share_requested)

    def _create_input_page(self, employees: list[EmployeeInfo]) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        group = QGroupBox("اطلاعات دوره محاسبه")
        group.setFont(FontManager.get_font(size=12, bold=True))
        form = QFormLayout(group)

        self.employee_combo = QComboBox()
        for emp in employees:
            self.employee_combo.addItem(emp.full_name, emp.employee_id)

        self.start_date_input = DataDatePicker()
        self.end_date_input = DataDatePicker()
        self.overtime_input = QSpinBox(maximum=100)

        form.addRow("انتخاب کارمند:", self.employee_combo)
        form.addRow("از تاریخ:", self.start_date_input)
        form.addRow("تا تاریخ:", self.end_date_input)
        form.addRow("ساعات اضافه کار:", self.overtime_input)

        layout.addWidget(group)
        layout.addStretch()
        return page

    def _on_generate_clicked(self):
        # Add basic validation
        if not self.start_date_input.get_date() or not self.end_date_input.get_date():
            show_warning_message_box(self, "خطا", "لطفا بازه زمانی را به طور کامل مشخص کنید.")
            return

        inputs = {
            'employee_id': self.employee_combo.currentData(),
            'start_date': self.start_date_input.get_date(),
            'end_date': self.end_date_input.get_date(),
            'overtime_hours': self.overtime_input.value()
        }
        self.generate_requested.emit(inputs)

    def show_preview(self, payslip_data: PayslipData):
        """Switches to the preview page and populates it."""
        self.payslip_preview.populate(payslip_data)
        self.stacked_widget.setCurrentWidget(self.payslip_preview)

        self.setWindowTitle(f"پیش‌نمایش فیش حقوقی: {payslip_data.employee_name}")
        self.generate_btn.setVisible(False)
        self.print_btn.setVisible(True)
        self.share_btn.setVisible(True)
