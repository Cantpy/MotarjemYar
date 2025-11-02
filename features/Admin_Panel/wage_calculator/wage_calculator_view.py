# features/Admin_Panel/wage_calculator/wage_calculator_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget,
                               QHeaderView, QTableWidgetItem, QComboBox, QAbstractItemView)
from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
import qtawesome as qta
import jdatetime
from shared.fonts.font_manager import FontManager
from shared.utils.persian_tools import to_persian_numbers, to_english_numbers
from features.Admin_Panel.wage_calculator.wage_calculator_models import PayrollRunEmployee, PayslipData
from features.Admin_Panel.wage_calculator_preview.salary_slip_viewer import SalarySlipViewer
from features.Admin_Panel.wage_calculator.wage_calculator_styles import WAGE_CALCULATOR_STYLES


class WageCalculatorView(QWidget):
    """
    The main view for the Wage Calculator feature. It now supports viewing
    payslips by double-clicking a row.
    """
    period_changed = Signal(dict)
    run_payroll_requested = Signal()
    view_payslip_requested = Signal(str)
    refresh_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WageCalculatorView")
        self._employee_data_map = {}
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # --- Top Bar ---
        top_bar_layout = self._create_top_bar()
        main_layout.addLayout(top_bar_layout)

        # --- Main Area (Table only) ---
        self.employee_table = self._create_employee_table()
        main_layout.addWidget(self.employee_table, 1)

        # --- Connections ---
        self.year_combo.currentIndexChanged.connect(self._on_period_changed)
        self.month_combo.currentIndexChanged.connect(self._on_period_changed)
        self.run_payroll_btn.clicked.connect(self.run_payroll_requested.emit)
        self.refresh_btn.clicked.connect(self.refresh_requested.emit)
        self.employee_table.itemDoubleClicked.connect(self._on_employee_double_clicked)

        self.setStyleSheet(WAGE_CALCULATOR_STYLES)

    def _create_top_bar(self):
        top_bar_layout = QHBoxLayout()
        today = jdatetime.date.today()
        self.year_combo = QComboBox()
        self.year_combo.addItems([to_persian_numbers(y) for y in range(today.year - 2, today.year + 2)])
        self.year_combo.setCurrentText(to_persian_numbers(today.year))

        self.month_combo = QComboBox()
        self.month_combo.addItems(
            ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"])
        self.month_combo.setCurrentIndex(today.month - 1)

        self.run_payroll_btn = QPushButton("ایجاد فیش حقوقی جدید")
        self.run_payroll_btn.setIcon(qta.icon('fa5s.cogs', color='white'))
        self.run_payroll_btn.setObjectName("runPayrollButton")

        self.refresh_btn = QPushButton(" بروزرسانی")
        self.refresh_btn.setIcon(qta.icon('fa5s.sync-alt', color='white'))
        self.refresh_btn.setObjectName("refreshButton")

        top_bar_layout.addWidget(QLabel("دوره پرداخت:"))
        top_bar_layout.addWidget(self.year_combo)
        top_bar_layout.addWidget(self.month_combo)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.refresh_btn)
        top_bar_layout.addWidget(self.run_payroll_btn)
        return top_bar_layout

    def _create_employee_table(self):
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["نام کارمند", "درآمد ناخالص", "خالص پرداختی", "وضعیت"])
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setToolTip("برای مشاهده فیش حقوقی نهایی شده، روی ردیف مورد نظر دو بار کلیک کنید.")
        return table

    def _on_period_changed(self):
        year = int(to_english_numbers(self.year_combo.currentText()))
        month = self.month_combo.currentIndex() + 1
        self.period_changed.emit({"year": year, "month": month})

    def _on_employee_double_clicked(self, item):
        selected_row = item.row()
        if selected_row < 0:
            return
        record = self._employee_data_map.get(selected_row)
        # Only emit if the payslip has been finalized and has an ID
        if record and record.payroll_id:
            self.view_payslip_requested.emit(record.payroll_id)

    def populate_table(self, records: list[PayrollRunEmployee]):
        self._employee_data_map = {row: rec for row, rec in enumerate(records)}
        self.employee_table.setRowCount(len(records))
        for row, rec in enumerate(records):
            self.employee_table.setItem(row, 0, QTableWidgetItem(rec.full_name))
            self.employee_table.setItem(row, 1, QTableWidgetItem(to_persian_numbers(f"{rec.gross_income:,.0f}")))
            self.employee_table.setItem(row, 2, QTableWidgetItem(to_persian_numbers(f"{rec.net_income:,.0f}")))

            status_item = QTableWidgetItem(rec.status)
            if rec.status == "نهایی شده":
                status_item.setForeground(QColor("#006400"))  # Dark Green
            else:
                status_item.setForeground(QColor("#808080"))  # Gray
            self.employee_table.setItem(row, 3, status_item)
