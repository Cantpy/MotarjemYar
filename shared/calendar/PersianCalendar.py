"""
Create a customized Persian calendar for the user to choose the delivery date
"""

from PySide6.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QComboBox, QDialogButtonBox,
                               QMessageBox, QVBoxLayout)
from PySide6.QtCore import Qt
import jdatetime


class CalendarDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("انتخاب تاریخ ارسال")

        layout = QVBoxLayout()

        # Month and Year Selectors
        self.year_combo = QComboBox()
        self.month_combo = QComboBox()

        # Populate year combo (current year to +2 years)
        current_year = jdatetime.date.today().year
        for year in range(current_year, current_year + 3):  # Current year to +2 years
            self.year_combo.addItem(str(year), year)

        # Populate month combo
        persian_months = [
            "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
            "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
        ]
        for i, month_name in enumerate(persian_months, start=1):
            self.month_combo.addItem(month_name, i)

        # Set initial selections
        today = jdatetime.date.today()
        self.year_combo.setCurrentText(str(today.year))
        self.month_combo.setCurrentIndex(today.month - 1)

        # Connect signals
        self.year_combo.currentIndexChanged.connect(self.update_calendar)
        self.month_combo.currentIndexChanged.connect(self.update_calendar)

        layout.addWidget(self.year_combo)
        layout.addWidget(self.month_combo)

        # Persian Calendar
        self.calendar = PersianCalendarWidget()
        layout.addWidget(self.calendar)

        # ComboBox for selecting hour
        self.hour_combo = QComboBox()
        self.hour_combo.addItem("ساعت مشخص نشده است")  # Default option
        for hour in range(8, 19):
            self.hour_combo.addItem(f"{hour:02d}:00")
        layout.addWidget(self.hour_combo)

        # Dialog buttons
        self.dialog_buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.dialog_buttons.accepted.connect(self.check_date_and_accept)
        self.dialog_buttons.rejected.connect(self.reject)
        layout.addWidget(self.dialog_buttons)

        self.setLayout(layout)

    def update_calendar(self):
        """Update the calendar when the year or month changes."""
        year = self.year_combo.currentData()
        month = self.month_combo.currentData()

        # Block invalid months before today
        today = jdatetime.date.today()
        if year == today.year and month < today.month:
            self.show_warning("ماه انتخابی قبل از تاریخ امروز است و مجاز نیست.")
            self.month_combo.setCurrentIndex(today.month - 1)
            return

        self.calendar.set_month_and_year(year, month)

    def check_date_and_accept(self):
        """Validate the selected date before accepting the dialog."""
        selected_date = self.calendar.get_selected_date()

        if selected_date and selected_date < jdatetime.date.today():
            self.show_warning("تاریخ انتخابی قبل از امروز است و مجاز نیست.")
            return

        self.accept()

    def show_warning(self, message):
        """Show a warning message box."""
        QMessageBox.warning(self, "هشدار", message)

    def get_selected_date_time(self):
        """Get the selected date and time."""
        selected_date = self.calendar.get_selected_date()
        selected_hour = self.hour_combo.currentText()

        if not selected_date:
            return None

        # Format date and time
        date_str = f"{selected_date.year}/{selected_date.month:02d}/{selected_date.day:02d}"
        if selected_hour != "ساعت مشخص نشده است":
            date_str += f" - {selected_hour}"
        return date_str


class PersianCalendarWidget(QTableWidget):
    def __init__(self):
        super().__init__()

        self.setRowCount(6)  # Maximum weeks in a month
        self.setColumnCount(7)  # Days of the week

        # Set headers for weekdays
        self.setHorizontalHeaderLabels(["ش", "ی", "د", "س", "چ", "پ", "ج"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)

        # Initialize current date
        self.current_date = jdatetime.date.today()

        self.populate_calendar()

    def populate_calendar(self):
        """Populate the calendar with days of the current Persian month."""
        self.clearContents()

        # First day of the Persian month
        first_day = self.current_date.replace(day=1)

        # Find the total days in the current month
        if first_day.month == 12:  # Handle Esfand month for leap years
            next_month = first_day.replace(year=first_day.year + 1, month=1, day=1)
        else:
            next_month = first_day.replace(month=first_day.month + 1, day=1)

        last_day_of_month = next_month - jdatetime.timedelta(days=1)
        total_days = last_day_of_month.day

        start_day_of_week = first_day.weekday()  # Persian weekday index

        row, col = 0, start_day_of_week
        for day in range(1, total_days + 1):
            cell_date = first_day.replace(day=day)
            item = QTableWidgetItem(str(day))

            # Disable dates before today
            if cell_date < jdatetime.date.today():
                item.setFlags(Qt.ItemIsEnabled)
                item.setForeground(Qt.gray)

            # Highlight today
            if cell_date == jdatetime.date.today():
                item.setBackground(Qt.yellow)

            self.setItem(row, col, item)
            col += 1
            if col > 6:  # Move to the next row if the week is full
                col = 0
                row += 1

    def set_month_and_year(self, year, month):
        """Set the calendar to a specific Persian year and month."""
        self.current_date = jdatetime.date(year, month, 1)
        self.populate_calendar()

    def get_selected_date(self):
        """Return the currently selected date as a `jdatetime.date` object."""
        selected_items = self.selectedItems()
        if selected_items:
            day = int(selected_items[0].text())
            return self.current_date.replace(day=day)
        return None
