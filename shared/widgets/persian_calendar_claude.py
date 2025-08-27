# shared/widgets/persian_calendar_claude.py

import sys
from datetime import datetime, timedelta, date
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                               QLineEdit, QPushButton, QCalendarWidget, QDialog,
                               QLabel, QComboBox, QGridLayout, QSpinBox, QCheckBox,
                               QButtonGroup, QRadioButton, QFrame, QScrollArea)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont, QPalette


class PersianDateConverter:
    """Handles conversion between Gregorian and Persian (Jalali) dates"""

    # Persian month names
    PERSIAN_MONTHS = [
        'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
        'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
    ]

    # Days of week in Persian
    PERSIAN_WEEKDAYS = [
        'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه', 'شنبه'
    ]

    @staticmethod
    def persian_to_english_digits(persian_str):
        """Convert Persian digits to English digits"""
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        english_digits = '0123456789'
        for p, e in zip(persian_digits, english_digits):
            persian_str = persian_str.replace(p, e)
        return persian_str

    @staticmethod
    def english_to_persian_digits(english_str):
        """Convert English digits to Persian digits"""
        english_digits = '0123456789'
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        for e, p in zip(english_digits, persian_digits):
            english_str = english_str.replace(e, p)
        return english_str

    @staticmethod
    def is_leap_persian(year):
        """Check if a Persian year is leap"""
        breaks = [
            -61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210,
            1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178
        ]

        jp = breaks[0]
        jump = 0
        for j in range(1, len(breaks)):
            jm = breaks[j]
            jump = jm - jp
            if year < jm:
                break
            jp = jm

        n = year - jp

        if jump - n < 6:
            n = n - jump + ((jump + 4) // 6) * 6

        leap = ((n + 1) % 33) % 4
        if jump == 33 and leap == 1:
            leap = 0

        return leap == 1

    @staticmethod
    def persian_to_gregorian(py, pm, pd):
        """Convert Persian date to Gregorian"""
        # Simplified conversion algorithm
        # This is a basic implementation - for production use, consider using a library like jdatetime

        # Calculate total days from Persian epoch
        total_days = 0

        # Add days for complete years
        for y in range(1, py):
            if PersianDateConverter.is_leap_persian(y):
                total_days += 366
            else:
                total_days += 365

        # Add days for complete months in current year
        for m in range(1, pm):
            if m <= 6:
                total_days += 31
            elif m <= 11:
                total_days += 30
            else:  # month 12
                if PersianDateConverter.is_leap_persian(py):
                    total_days += 30
                else:
                    total_days += 29

        # Add remaining days
        total_days += pd - 1

        # Persian epoch in Gregorian calendar (March 22, 622 CE)
        persian_epoch = date(622, 3, 22)
        result_date = persian_epoch + timedelta(days=total_days)

        return result_date

    @staticmethod
    def gregorian_to_persian(g_date):
        """Convert Gregorian date to Persian"""
        # Simplified conversion - this is a basic implementation
        # For production use, consider using jdatetime library

        persian_epoch = date(622, 3, 22)
        days_diff = (g_date - persian_epoch).days

        # Approximate calculation
        year = 1
        while days_diff >= (366 if PersianDateConverter.is_leap_persian(year) else 365):
            if PersianDateConverter.is_leap_persian(year):
                days_diff -= 366
            else:
                days_diff -= 365
            year += 1

        # Find month
        month = 1
        while True:
            if month <= 6:
                month_days = 31
            elif month <= 11:
                month_days = 30
            else:  # month 12
                month_days = 30 if PersianDateConverter.is_leap_persian(year) else 29

            if days_diff < month_days:
                break

            days_diff -= month_days
            month += 1

        day = days_diff + 1

        return year, month, day


class PersianCalendarDialog(QDialog):
    """Persian Calendar Dialog with different modes"""

    date_selected = Signal(object)  # Emits selected date/datetime info

    def __init__(self, parent=None, mode="birth", initial_date=None):
        super().__init__(parent)
        self.mode = mode  # "birth", "invoice", "data_range"
        self.selected_dates = []  # For range selection
        self.converter = PersianDateConverter()

        self.setWindowTitle("تقویم فارسی")
        self.setModal(True)
        self.resize(400, 500)

        # Get current Persian date
        today = date.today()
        self.current_py, self.current_pm, self.current_pd = self.converter.gregorian_to_persian(today)

        # Set initial date
        if initial_date:
            if isinstance(initial_date, (date, datetime)):
                self.py, self.pm, self.pd = self.converter.gregorian_to_persian(
                    initial_date.date() if isinstance(initial_date, datetime) else initial_date)
            else:
                self.py, self.pm, self.pd = self.current_py, self.current_pm, self.current_pd
        else:
            self.py, self.pm, self.pd = self.current_py, self.current_pm, self.current_pd

        self.setup_ui()
        self.update_calendar()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Title
        title_label = QLabel(self.get_mode_title())
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Year and month selection
        year_month_layout = QHBoxLayout()

        # Year selection
        self.year_combo = QComboBox()
        self.setup_year_combo()
        self.year_combo.currentTextChanged.connect(self.on_year_changed)
        year_month_layout.addWidget(QLabel("سال:"))
        year_month_layout.addWidget(self.year_combo)

        # Month selection
        self.month_combo = QComboBox()
        for i, month in enumerate(self.converter.PERSIAN_MONTHS):
            self.month_combo.addItem(month)
        self.month_combo.setCurrentIndex(self.pm - 1)
        self.month_combo.currentIndexChanged.connect(self.on_month_changed)
        year_month_layout.addWidget(QLabel("ماه:"))
        year_month_layout.addWidget(self.month_combo)

        layout.addLayout(year_month_layout)

        # Calendar grid
        self.calendar_widget = QWidget()
        self.calendar_layout = QGridLayout()
        self.calendar_widget.setLayout(self.calendar_layout)
        layout.addWidget(self.calendar_widget)

        # Time selection for invoice mode
        if self.mode == "invoice":
            time_layout = QHBoxLayout()
            time_layout.addWidget(QLabel("ساعت:"))
            self.hour_combo = QComboBox()
            for hour in range(8, 19):  # 8 AM to 6 PM
                self.hour_combo.addItem(f"{hour:02d}")
            self.hour_combo.setCurrentIndex(0)
            time_layout.addWidget(self.hour_combo)

            time_layout.addWidget(QLabel("دقیقه:"))
            self.minute_combo = QComboBox()
            for minute in [0, 15, 30, 45]:
                self.minute_combo.addItem(f"{minute:02d}")
            time_layout.addWidget(self.minute_combo)

            layout.addLayout(time_layout)

        # Range selection info for data mode
        if self.mode == "data_range":
            self.range_label = QLabel("برای انتخاب بازه، روی دو تاریخ کلیک کنید")
            self.range_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.range_label)

            self.selected_range_label = QLabel("")
            self.selected_range_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.selected_range_label)

        # Buttons
        button_layout = QHBoxLayout()

        if self.mode == "data_range":
            clear_button = QPushButton("پاک کردن")
            clear_button.clicked.connect(self.clear_selection)
            button_layout.addWidget(clear_button)

        ok_button = QPushButton("تایید")
        ok_button.clicked.connect(self.accept_selection)
        cancel_button = QPushButton("لغو")
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def get_mode_title(self):
        titles = {
            "birth": "انتخاب تاریخ تولد",
            "invoice": "انتخاب تاریخ تحویل فاکتور",
            "data_range": "انتخاب بازه تاریخ"
        }
        return titles.get(self.mode, "تقویم فارسی")

    def setup_year_combo(self):
        self.year_combo.clear()

        if self.mode == "birth":
            # 90 years back from current Persian year
            start_year = self.current_py - 90
            end_year = self.current_py
            for year in range(end_year, start_year - 1, -1):
                persian_year = self.converter.english_to_persian_digits(str(year))
                self.year_combo.addItem(persian_year)

        elif self.mode == "invoice":
            # Current and next year only
            for year in [self.current_py, self.current_py + 1]:
                persian_year = self.converter.english_to_persian_digits(str(year))
                self.year_combo.addItem(persian_year)

        else:  # data_range
            # Wide range for data purposes
            start_year = self.current_py - 10
            end_year = self.current_py + 5
            for year in range(end_year, start_year - 1, -1):
                persian_year = self.converter.english_to_persian_digits(str(year))
                self.year_combo.addItem(persian_year)

        # Set current selection
        current_persian_year = self.converter.english_to_persian_digits(str(self.py))
        index = self.year_combo.findText(current_persian_year)
        if index >= 0:
            self.year_combo.setCurrentIndex(index)

    def on_year_changed(self, year_text):
        english_year = self.converter.persian_to_english_digits(year_text)
        self.py = int(english_year)
        self.update_calendar()

    def on_month_changed(self, month_index):
        self.pm = month_index + 1
        self.update_calendar()

    def update_calendar(self):
        # Clear existing calendar
        for i in reversed(range(self.calendar_layout.count())):
            self.calendar_layout.itemAt(i).widget().setParent(None)

        # Add weekday headers
        weekdays = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج']
        for i, day in enumerate(weekdays):
            label = QLabel(day)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-weight: bold; background-color: #f0f0f0; padding: 5px;")
            self.calendar_layout.addWidget(label, 0, i)

        # Calculate days in month
        if self.pm <= 6:
            days_in_month = 31
        elif self.pm <= 11:
            days_in_month = 30
        else:  # month 12
            days_in_month = 30 if self.converter.is_leap_persian(self.py) else 29

        # Find first day of month (simplified - assuming Saturday is 0)
        first_day_gregorian = self.converter.persian_to_gregorian(self.py, self.pm, 1)
        first_day_weekday = (first_day_gregorian.weekday() + 2) % 7  # Adjust for Persian week

        # Add calendar days
        row = 1
        col = first_day_weekday

        for day in range(1, days_in_month + 1):
            button = QPushButton(self.converter.english_to_persian_digits(str(day)))
            button.setFixedSize(40, 40)
            button.clicked.connect(lambda checked, d=day: self.on_day_selected(d))

            # Style based on mode and date validity
            if self.is_date_selectable(day):
                if self.mode == "data_range" and (self.py, self.pm, day) in [(d[0], d[1], d[2]) for d in
                                                                             self.selected_dates]:
                    button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
                else:
                    button.setStyleSheet("background-color: white; border: 1px solid #ccc;")
            else:
                button.setStyleSheet("background-color: #f5f5f5; color: #ccc;")
                button.setEnabled(False)

            self.calendar_layout.addWidget(button, row, col)

            col += 1
            if col > 6:
                col = 0
                row += 1

    def is_date_selectable(self, day):
        """Check if a date is selectable based on mode constraints"""
        if self.mode == "birth":
            return True  # All dates in valid range are selectable

        elif self.mode == "invoice":
            # Cannot select dates before today
            selected_gregorian = self.converter.persian_to_gregorian(self.py, self.pm, day)
            return selected_gregorian >= date.today()

        else:  # data_range
            return True  # All dates are selectable for data range

    def on_day_selected(self, day):
        if self.mode == "data_range":
            # Handle range selection
            date_tuple = (self.py, self.pm, day)
            if date_tuple in [(d[0], d[1], d[2]) for d in self.selected_dates]:
                # Remove if already selected
                self.selected_dates = [d for d in self.selected_dates if
                                       not (d[0] == self.py and d[1] == self.pm and d[2] == day)]
            else:
                # Add to selection
                self.selected_dates.append((self.py, self.pm, day))
                if len(self.selected_dates) > 2:
                    self.selected_dates = self.selected_dates[-2:]  # Keep only last 2

            self.update_range_display()
            self.update_calendar()
        else:
            # Single date selection
            self.pd = day
            self.accept_selection()

    def update_range_display(self):
        if len(self.selected_dates) == 2:
            date1 = self.selected_dates[0]
            date2 = self.selected_dates[1]
            # Ensure correct order
            if (date1[0], date1[1], date1[2]) > (date2[0], date2[1], date2[2]):
                date1, date2 = date2, date1

            date1_str = self.format_persian_date(date1[0], date1[1], date1[2])
            date2_str = self.format_persian_date(date2[0], date2[1], date2[2])
            self.selected_range_label.setText(f"از {date1_str} تا {date2_str}")
        elif len(self.selected_dates) == 1:
            date_str = self.format_persian_date(self.selected_dates[0][0], self.selected_dates[0][1],
                                                self.selected_dates[0][2])
            self.selected_range_label.setText(f"انتخاب شده: {date_str}")
        else:
            self.selected_range_label.setText("")

    def clear_selection(self):
        self.selected_dates.clear()
        self.update_range_display()
        self.update_calendar()

    def format_persian_date(self, year, month, day, include_time=False, hour=None, minute=None):
        """Format date in Persian YYYY/MM/DD format"""
        date_str = f"{year:04d}/{month:02d}/{day:02d}"
        if include_time and hour is not None and minute is not None:
            date_str += f" {hour:02d}:{minute:02d}"
        return self.converter.english_to_persian_digits(date_str)

    def accept_selection(self):
        if self.mode == "data_range":
            if len(self.selected_dates) < 2:
                return  # Need 2 dates for range

            # Sort dates
            dates = sorted(self.selected_dates, key=lambda x: (x[0], x[1], x[2]))
            result = {
                'mode': self.mode,
                'start_date': dates[0],
                'end_date': dates[1],
                'formatted': f"از {self.format_persian_date(*dates[0])} تا {self.format_persian_date(*dates[1])}"
            }

        elif self.mode == "invoice":
            hour = int(self.hour_combo.currentText()) if hasattr(self, 'hour_combo') else 8
            minute = int(self.minute_combo.currentText()) if hasattr(self, 'minute_combo') else 0

            result = {
                'mode': self.mode,
                'date': (self.py, self.pm, self.pd),
                'time': (hour, minute),
                'formatted': self.format_persian_date(self.py, self.pm, self.pd, True, hour, minute)
            }

        else:  # birth
            result = {
                'mode': self.mode,
                'date': (self.py, self.pm, self.pd),
                'formatted': self.format_persian_date(self.py, self.pm, self.pd)
            }

        self.date_selected.emit(result)
        self.accept()


class PersianDateLineEdit(QLineEdit):
    """Line edit that opens Persian calendar on click"""

    def __init__(self, mode="birth", parent=None):
        super().__init__(parent)
        self.mode = mode
        self.setReadOnly(True)
        self.setPlaceholderText("برای انتخاب تاریخ کلیک کنید")
        self.selected_data = None

    def mousePressEvent(self, event):
        self.open_calendar()
        super().mousePressEvent(event)

    def open_calendar(self):
        dialog = PersianCalendarDialog(self, self.mode)
        dialog.date_selected.connect(self.on_date_selected)
        dialog.exec()

    def on_date_selected(self, date_data):
        self.selected_data = date_data
        self.setText(date_data['formatted'])

    def get_selected_data(self):
        return self.selected_data


# Demo application
class DemoWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Persian Calendar Demo")
        self.setGeometry(100, 100, 600, 300)

        layout = QVBoxLayout()

        # Birth date
        layout.addWidget(QLabel("تاریخ تولد:"))
        self.birth_date_edit = PersianDateLineEdit("birth")
        layout.addWidget(self.birth_date_edit)

        # Invoice date
        layout.addWidget(QLabel("تاریخ تحویل فاکتور:"))
        self.invoice_date_edit = PersianDateLineEdit("invoice")
        layout.addWidget(self.invoice_date_edit)

        # Data range
        layout.addWidget(QLabel("بازه تاریخ داده‌ها:"))
        self.data_range_edit = PersianDateLineEdit("data_range")
        layout.addWidget(self.data_range_edit)

        # Show selected data button
        show_data_btn = QPushButton("نمایش داده‌های انتخاب شده")
        show_data_btn.clicked.connect(self.show_selected_data)
        layout.addWidget(show_data_btn)

        # Output area
        self.output_label = QLabel()
        self.output_label.setWordWrap(True)
        self.output_label.setStyleSheet("background-color: #f9f9f9; padding: 10px; border: 1px solid #ccc;")
        layout.addWidget(self.output_label)

        self.setLayout(layout)

    def show_selected_data(self):
        output = "داده‌های انتخاب شده:\n"

        birth_data = self.birth_date_edit.get_selected_data()
        if birth_data:
            output += f"تاریخ تولد: {birth_data['formatted']}\n"

        invoice_data = self.invoice_date_edit.get_selected_data()
        if invoice_data:
            output += f"تاریخ تحویل فاکتور: {invoice_data['formatted']}\n"

        data_range = self.data_range_edit.get_selected_data()
        if data_range:
            output += f"بازه داده‌ها: {data_range['formatted']}\n"

        self.output_label.setText(output)



if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set RTL layout
    app.setLayoutDirection(Qt.RightToLeft)

    window = DemoWindow()
    window.show()

    sys.exit(app.exec())