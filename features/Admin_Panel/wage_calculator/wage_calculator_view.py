# Admin_Panel/wage_calculator/wage_calculator_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QTableWidget,
                               QHeaderView, QTableWidgetItem, QGridLayout, QSpinBox, QGroupBox, QFormLayout,
                               QComboBox)
from PySide6.QtCore import Qt, Signal, QDate
import qtawesome as qta
from shared.widgets.custom_widgets import create_stat_card
from shared.widgets.persian_calendar import DataDatePicker      # Using your custom date picker
from shared.fonts.font_manager import FontManager
from .wage_calculator_models import EmployeeData, PayrollStats, RoleSummaryData
from shared import to_persian_number
import jdatetime  # For getting the current Jalali month


class WageCalculatorView(QWidget):
    calculation_requested = Signal(EmployeeData)
    perform_calculation_requested = Signal(dict)
    month_changed = Signal(int)  # Emits the month number (1-12)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_calc_payment_type = None
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # --- 1. Title ---
        title_layout = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(qta.icon('fa5s.money-check-alt', color='#28a745').pixmap(48, 48))
        title_label = QLabel("محاسبه حقوق و دستمزد")
        title_label.setFont(FontManager.get_font(size=18, bold=True))
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        main_layout.addLayout(title_layout)

        self.month_combo = QComboBox()
        persian_months = [
            "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
            "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
        ]
        for i, name in enumerate(persian_months, 1):
            self.month_combo.addItem(name, i)

        # Set to current Jalali month
        current_j_month = jdatetime.date.today().month
        self.month_combo.setCurrentIndex(current_j_month - 1)

        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(QLabel("برای ماه:"))
        title_layout.addWidget(self.month_combo)
        main_layout.addLayout(title_layout)

        self.month_combo.currentIndexChanged.connect(self._on_month_changed)

        # --- 2. Stat Cards ---
        stats_layout = QGridLayout()
        self.card_total_employees = create_stat_card("کل کارکنان فعال", "#17a2b8")
        self.card_total_payroll = create_stat_card("کل حقوق ماه (تخمینی)", "#d9534f")
        self.card_avg_salary = create_stat_card("میانگین حقوق (تخمینی)", "#ffc107")
        stats_layout.addWidget(self.card_total_employees, 0, 0)
        stats_layout.addWidget(self.card_total_payroll, 0, 1)
        stats_layout.addWidget(self.card_avg_salary, 0, 2)
        main_layout.addLayout(stats_layout)

        # --- 3. Main Area: Table and Calculation Panel ---
        main_area_layout = QHBoxLayout()
        main_layout.addLayout(main_area_layout, 1)

        self.employee_table = QTableWidget()
        self.employee_table.setColumnCount(5)
        self.employee_table.setHorizontalHeaderLabels(["نام کامل", "نقش", "نوع پرداخت", "جزئیات پرداخت", ""])
        self.employee_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_area_layout.addWidget(self.employee_table, 2)

        self.calc_panel = QFrame()
        self.calc_panel.setFrameShape(QFrame.StyledPanel)
        self.calc_panel.setVisible(False)
        self.calc_panel_layout = QVBoxLayout(self.calc_panel)
        main_area_layout.addWidget(self.calc_panel, 1)

        # --- 4. Bottom Summary Section ---
        summary_container = QGroupBox("خلاصه وضعیت نقش‌ها")
        summary_container.setFont(FontManager.get_font(size=12, bold=True))
        summary_layout = QHBoxLayout(summary_container)  # Use QHBoxLayout for side-by-side boxes
        main_layout.addWidget(summary_container)

        # A dictionary to hold the widgets for each role for easy updating
        self.summary_widgets = {}

        # Define the roles and their associated icons
        roles_to_display = {
            "admin": {"title": "مدیران", "icon": "fa5s.user-shield"},
            "clerk": {"title": "کارمندان", "icon": "fa5s.user-edit"},
            "translator": {"title": "مترجمان", "icon": "fa5s.language"},
            "accountant": {"title": "حسابداران", "icon": "fa5s.file-invoice-dollar"}
        }

        for key, info in roles_to_display.items():
            role_box, labels = self._create_role_summary_box(info['title'], info['icon'])
            summary_layout.addWidget(role_box)
            self.summary_widgets[key] = labels

    def _create_role_summary_box(self, title: str, icon_name: str) -> tuple[QGroupBox, dict]:
        """Factory method to create a single styled summary groupbox."""
        box = QGroupBox()

        # Main layout for the box
        layout = QVBoxLayout(box)
        layout.setSpacing(10)

        # Header with icon and title
        header_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color='#555').pixmap(24, 24))
        title_label = QLabel(title)
        title_label.setFont(FontManager.get_font(size=12, bold=True))
        title_label.setStyleSheet("color: #333;")
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Form layout for the data
        form_layout = QFormLayout()
        form_layout.setContentsMargins(10, 5, 10, 5)
        form_layout.setSpacing(8)

        count_label = QLabel("...")
        total_label = QLabel("...")
        average_label = QLabel("...")

        form_layout.addRow("تعداد کارکنان:", count_label)
        form_layout.addRow("جمع حقوق پایه:", total_label)
        form_layout.addRow("میانگین حقوق پایه:", average_label)
        layout.addLayout(form_layout)

        # Return the box and a dictionary of its labels for easy access
        labels = {"count": count_label, "total": total_label, "average": average_label}
        return box, labels

    def populate_employee_table(self, employees: list[EmployeeData]):
        self.employee_table.clearContents()
        self.employee_table.setRowCount(len(employees))
        for row, emp in enumerate(employees):
            self.employee_table.setItem(row, 0, QTableWidgetItem(emp.full_name))
            self.employee_table.setItem(row, 1, QTableWidgetItem(emp.role))
            self.employee_table.setItem(row, 2, QTableWidgetItem(emp.payment_type))
            self.employee_table.setItem(row, 3, QTableWidgetItem(emp.payment_detail))

            calc_btn = QPushButton("محاسبه")
            calc_btn.clicked.connect(lambda chk, e=emp: self.calculation_requested.emit(e))
            self.employee_table.setCellWidget(row, 4, calc_btn)

    def show_calculation_panel(self, employee: EmployeeData):
        """Dynamically builds the calculation input panel."""
        self._clear_layout(self.calc_panel_layout)

        # --- FIX: Store the payment type as the current context ---
        self._current_calc_payment_type = employee.payment_type

        title = QLabel(f"<b>محاسبه برای: {employee.full_name}</b>")
        self.calc_panel_layout.addWidget(title)

        form_layout = QFormLayout()
        if employee.payment_type == 'Fixed':
            self.overtime_input = QSpinBox(maximum=100)
            self.children_input = QSpinBox(maximum=10)
            form_layout.addRow("ساعات اضافه کار:", self.overtime_input)
            form_layout.addRow("تعداد فرزندان:", self.children_input)
        elif employee.payment_type == 'Commission':
            self.start_date_input = DataDatePicker()
            self.end_date_input = DataDatePicker()
            form_layout.addRow("از تاریخ:", self.start_date_input)
            form_layout.addRow("تا تاریخ:", self.end_date_input)

        self.calc_panel_layout.addLayout(form_layout)

        self.result_details_label = QLabel("...")
        self.result_total_label = QLabel("<b>جمع نهایی: ...</b>")
        self.calc_panel_layout.addWidget(self.result_details_label)
        self.calc_panel_layout.addWidget(self.result_total_label)

        confirm_btn = QPushButton("محاسبه کن")
        confirm_btn.clicked.connect(lambda: self.perform_calculation_requested.emit(self.get_calculation_inputs()))
        self.calc_panel_layout.addWidget(confirm_btn)
        self.calc_panel_layout.addStretch()

        self.calc_panel.setVisible(True)

    def get_calculation_inputs(self) -> dict:
        """Reads values from the panel based on the stored context."""
        inputs = {}
        # --- FIX: Use the stored state variable, not hasattr ---
        # This is a robust check that is guaranteed to be correct.
        if self._current_calc_payment_type == 'Fixed':
            inputs['overtime_hours'] = self.overtime_input.value()
            inputs['num_children'] = self.children_input.value()
        elif self._current_calc_payment_type == 'Commission':
            start_date = self.start_date_input.get_date()
            end_date = self.end_date_input.get_date()
            inputs['start_date'] = start_date
            inputs['end_date'] = end_date
        return inputs

    def display_calculation_result(self, result):
        self.result_details_label.setText(result.details)
        self.result_total_label.setText(f"<b>جمع نهایی: {result.total_wage:,.0f} تومان</b>")

    def update_payroll_stats(self, stats: PayrollStats):
        """Updates the top-level KPI cards."""
        self.card_total_employees.findChild(QLabel, "statValue").setText(
            to_persian_number(stats.total_employees) + " نفر"
        )
        self.card_total_payroll.findChild(QLabel, "statValue").setText(
            f"{to_persian_number(f'{stats.total_payroll_month:,.0f}')} تومان"
        )
        self.card_avg_salary.findChild(QLabel, "statValue").setText(
            f"{to_persian_number(f'{stats.average_salary_month:,.0f}')} تومان"
        )

    def update_role_summary(self, summary_data: list[RoleSummaryData]):
        """
        Updates the four summary groupboxes with calculated data.
        """
        for data_item in summary_data:
            role_key = data_item.role_key
            if role_key in self.summary_widgets:
                labels = self.summary_widgets[role_key]

                labels['count'].setText(to_persian_number(data_item.count))

                if data_item.count == 0:
                    labels['total'].setText("-")
                    labels['average'].setText("-")
                elif data_item.total_salary > 0:
                    labels['total'].setText(f"{to_persian_number(f'{data_item.total_salary:,.0f}')} تومان")
                    labels['average'].setText(f"{to_persian_number(f'{data_item.average_salary:,.0f}')} تومان")
                else:
                    labels['total'].setText("مبتنی بر کمیسیون")
                    labels['average'].setText("مبتنی بر کمیسیون")

    def _clear_layout(self, layout):
        """Removes and deletes all widgets from a layout."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            # If the item is a layout, recursively clear it
            elif item.layout() is not None:
                self._clear_layout(item.layout())

    def _on_month_changed(self):
        """Emits the new month's data when the user changes the selection."""
        month_data = self.month_combo.currentData()
        if month_data:
            self.month_changed.emit(month_data)
