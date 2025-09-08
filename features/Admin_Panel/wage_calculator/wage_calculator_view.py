# Admin_Panel/wage_calculator/wage_calculator_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                               QFrame, QTableWidget, QHeaderView, QTableWidgetItem,
                               QComboBox, QDialog, QSpinBox, QDialogButtonBox)
from PySide6.QtCore import Qt, Signal
import qtawesome as qta
import jdatetime
from shared.fonts.font_manager import FontManager
from shared.utils.persian_tools import to_persian_numbers, to_english_numbers
from features.Admin_Panel.wage_calculator.wage_calculator_models import PayrollRunEmployee, PayslipData
from features.Admin_Panel.wage_calculator.wage_calculator_styles import WAGE_CALCULATOR_STYLES


class WageCalculatorView(QWidget):
    """
    The main _view for the Wage Calculator feature.
    """
    period_changed = Signal(dict)
    run_payroll_requested = Signal()
    employee_selected = Signal(str)
    print_payslip_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WageCalculatorView")
        self._employee_data_map = {}
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        top_bar_layout = QHBoxLayout()
        today = jdatetime.date.today()
        self.year_combo = QComboBox()
        self.year_combo.addItems([to_persian_numbers(y) for y in range(today.year - 2, today.year + 2)])
        self.year_combo.setCurrentText(to_persian_numbers(today.year))

        self.month_combo = QComboBox()
        self.month_combo.addItems(
            ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"])
        self.month_combo.setCurrentIndex(today.month - 1)

        self.run_payroll_btn = QPushButton("اجرای محاسبه حقوق")
        self.run_payroll_btn.setIcon(qta.icon('fa5s.cogs', color='white'))
        self.run_payroll_btn.setObjectName("runPayrollButton")

        top_bar_layout.addWidget(QLabel("دوره پرداخت:"))
        top_bar_layout.addWidget(self.year_combo)
        top_bar_layout.addWidget(self.month_combo)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.run_payroll_btn)
        main_layout.addLayout(top_bar_layout)

        main_area_layout = QHBoxLayout()
        main_layout.addLayout(main_area_layout, 1)

        self.employee_table = QTableWidget()
        self.employee_table.setColumnCount(4)
        self.employee_table.setHorizontalHeaderLabels(["نام کارمند", "درآمد ناخالص", "خالص پرداختی", "وضعیت"])
        self.employee_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.employee_table.setSelectionMode(QTableWidget.SingleSelection)
        self.employee_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_area_layout.addWidget(self.employee_table, 2)

        self.payslip_panel = self._create_payslip_panel()
        self.payslip_panel.setVisible(False)
        main_area_layout.addWidget(self.payslip_panel, 1)

        self.year_combo.currentIndexChanged.connect(self._on_period_changed)
        self.month_combo.currentIndexChanged.connect(self._on_period_changed)
        self.run_payroll_btn.clicked.connect(self._on_run_payroll_btn_clicked)
        self.employee_table.itemSelectionChanged.connect(self._on_employee_selected)

        self.setStyleSheet(WAGE_CALCULATOR_STYLES)

    def _create_payslip_panel(self) -> QFrame:
        """
        Creates the right-side panel to display detailed payslip information.
        """
        panel = QFrame()
        panel.setObjectName("payslipPanel")
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)
        self.payslip_name = QLabel()
        self.payslip_period = QLabel()
        self.payslip_details = QLabel()
        self.payslip_details.setWordWrap(True)
        self.print_btn = QPushButton(" چاپ فیش")
        self.print_btn.setIcon(qta.icon('fa5s.print'))
        self.print_btn.clicked.connect(self.print_payslip_requested)
        layout.addWidget(self.payslip_name)
        layout.addWidget(self.payslip_period)
        layout.addWidget(self.payslip_details, 1)
        layout.addWidget(self.print_btn)
        return panel

    def _on_period_changed(self):
        """
        A simple handler method that just emits the signal to the controller.
        """
        year = int(to_english_numbers(self.year_combo.currentText()))
        month = self.month_combo.currentIndex() + 1
        self.period_changed.emit({"year": year, "month": month})
        self.payslip_panel.setVisible(False)

    def _on_run_payroll_btn_clicked(self):
        """
        A simple handler method that just emits the signal to the controller.
        It contains no complex logic.
        """
        self.run_payroll_requested.emit()

    def _on_employee_selected(self):
        """
        A simple handler method that just emits the signal to the controller.
        """
        selected_row = self.employee_table.currentRow()
        if selected_row < 0:
            return
        record = self._employee_data_map.get(selected_row)
        if record:
            self.employee_selected.emit(record.payroll_id)

    def populate_table(self, records: list[PayrollRunEmployee]):
        """
        Populates the main employee table with payroll summary data.
        """
        self._employee_data_map = {row: rec for row, rec in enumerate(records)}
        self.employee_table.setRowCount(len(records))
        for row, rec in enumerate(records):
            self.employee_table.setItem(row, 0, QTableWidgetItem(rec.full_name))
            self.employee_table.setItem(row, 1, QTableWidgetItem(to_persian_numbers(f"{rec.gross_income:,.0f}")))
            self.employee_table.setItem(row, 2, QTableWidgetItem(to_persian_numbers(f"{rec.net_income:,.0f}")))
            self.employee_table.setItem(row, 3, QTableWidgetItem(rec.status))

    def display_payslip_details(self, payslip: PayslipData):
        """
        Displays the detailed payslip information in the side panel.
        """
        self.payslip_name.setText(f"<b>{payslip.employee_name}</b>")
        self.payslip_period.setText(to_persian_numbers(payslip.pay_period_str))
        details_html = ""
        for comp in payslip.components:
            sign = "" if comp.type == 'Earning' else "-"
            details_html += f"<b>{comp.name}:</b> {sign}{to_persian_numbers(f'{comp.amount:,.0f}')}<br>"
        self.payslip_details.setText(details_html)
        self.payslip_panel.setVisible(True)
