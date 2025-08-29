# Admin_Panel/wage_calculator_preview/payslip_widget.py

from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                               QGridLayout, QGroupBox, QFormLayout)
from PySide6.QtCore import Qt
from shared.fonts.font_manager import FontManager
from shared.utils.persian_tools import to_persian_numbers
from features.Admin_Panel.wage_calculator.wage_calculator_models import PayslipData


class PayslipWidget(QFrame):
    """
    A self-contained widget designed to look like a modern, professional,
    and printable A5 landscape payslip. This is a pure display widget.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Approximate A5 Landscape pixels at 96 DPI (210x148mm)
        self.setFixedSize(794, 560)
        self.setObjectName("PayslipWidget")
        self.setStyleSheet("""
            #PayslipWidget {
                background-color: white;
                border: 1px solid #ddd;
                padding: 25px;
                color: #333;
            }
            QGroupBox {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top right;
                padding: 5px 10px;
                background-color: #f7f9fc;
                border-radius: 4px;
                color: #005A9E;
            }
        """)

        # --- Main Layout ---
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # --- 1. Header Section ---
        header_layout = QHBoxLayout()
        company_name = QLabel("<b>دفتر ترجمه رسمی مترجم‌یار</b>")
        company_name.setFont(FontManager.get_font(size=14))
        payslip_title = QLabel("فیش حقوقی")
        payslip_title.setFont(FontManager.get_font(size=16, bold=True))
        header_layout.addWidget(company_name)
        header_layout.addStretch()
        header_layout.addWidget(payslip_title)
        main_layout.addLayout(header_layout)

        # --- 2. Employee & Period Details ---
        details_frame = QFrame()
        details_layout = QGridLayout(details_frame)
        details_layout.setContentsMargins(0, 10, 0, 10)
        self.emp_name_label = QLabel("...")
        self.pay_period_label = QLabel("...")
        details_layout.addWidget(QLabel("<b>نام کارمند:</b>"), 0, 0)
        details_layout.addWidget(self.emp_name_label, 0, 1)
        details_layout.addWidget(QLabel("<b>دوره پرداخت:</b>"), 1, 0)
        details_layout.addWidget(self.pay_period_label, 1, 1)
        details_layout.setColumnStretch(1, 1)
        main_layout.addWidget(details_frame)

        main_layout.addWidget(self._create_separator())

        # --- 3. Body: Earnings & Deductions (Side-by-Side) ---
        body_layout = QHBoxLayout()
        main_layout.addLayout(body_layout, 1)  # Give vertical stretch

        # Earnings Box
        earnings_box = QGroupBox("درآمدها")
        self.earnings_layout = QFormLayout(earnings_box)
        self.earnings_layout.setHorizontalSpacing(20)
        body_layout.addWidget(earnings_box)

        # Deductions Box
        deductions_box = QGroupBox("کسورات")
        self.deductions_layout = QFormLayout(deductions_box)
        self.deductions_layout.setHorizontalSpacing(20)
        body_layout.addWidget(deductions_box)

        # --- 4. Footer: Totals ---
        totals_frame = QFrame()
        totals_frame.setObjectName("totalsFrame")
        totals_frame.setStyleSheet("#totalsFrame { border-top: 2px solid #0078D7; padding-top: 10px; }")
        totals_layout = QGridLayout(totals_frame)
        self.gross_income_label = QLabel("۰ تومان")
        self.total_deductions_label = QLabel("۰ تومان")
        self.net_income_label = QLabel("۰ تومان")
        self.net_income_label.setFont(FontManager.get_font(size=14, bold=True))
        self.net_income_label.setStyleSheet("color: #28a745;")

        totals_layout.addWidget(QLabel("جمع درآمد ناخالص:"), 0, 0)
        totals_layout.addWidget(self.gross_income_label, 0, 1, alignment=Qt.AlignLeft)
        totals_layout.addWidget(QLabel("جمع کسورات:"), 1, 0)
        totals_layout.addWidget(self.total_deductions_label, 1, 1, alignment=Qt.AlignLeft)
        totals_layout.addWidget(QLabel("خالص پرداختی:"), 2, 0)
        totals_layout.addWidget(self.net_income_label, 2, 1, alignment=Qt.AlignLeft)
        totals_layout.setColumnStretch(1, 1)
        main_layout.addLayout(totals_layout)

    def _create_separator(self) -> QFrame:
        """Helper to create a styled horizontal line."""
        line = QFrame();
        line.setFrameShape(QFrame.HLine);
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #eee;")
        return line

    def _clear_form_layout(self, layout: QFormLayout):
        """Safely removes all rows from a QFormLayout."""
        while layout.rowCount() > 0:
            layout.removeRow(0)

    def populate(self, payslip_data: PayslipData):
        """Fills the entire payslip with the calculated data from a DTO."""
        if not payslip_data:
            return

        # --- Populate Header and Details ---
        self.emp_name_label.setText(payslip_data.employee_name)
        self.pay_period_label.setText(to_persian_numbers(payslip_data.pay_period_str))

        # --- Clear and Populate Earnings & Deductions ---
        self._clear_form_layout(self.earnings_layout)
        self._clear_form_layout(self.deductions_layout)

        for component in payslip_data.components:
            value_label = QLabel(to_persian_numbers(f"{component.amount:,.0f}"))
            value_label.setLayoutDirection(Qt.LeftToRight)
            if component.type == 'Earning':
                self.earnings_layout.addRow(component.name, value_label)
            elif component.type == 'Deduction':
                self.deductions_layout.addRow(component.name, value_label)

        # --- Populate Footer Totals ---
        self.gross_income_label.setText(f"{to_persian_numbers(f'{payslip_data.gross_income:,.0f}')} تومان")
        self.total_deductions_label.setText(f"{to_persian_numbers(f'{payslip_data.total_deductions:,.0f}')} تومان")
        self.net_income_label.setText(f"{to_persian_numbers(f'{payslip_data.net_income:,.0f}')} تومان")
