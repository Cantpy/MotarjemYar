import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QLineEdit, QVBoxLayout, QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QGridLayout
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, Signal, QPoint
import jdatetime


def to_persian_number(text):
    """Converts only the English digit characters in a string to Persian digits."""
    english_digits = "0123456789"
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    translation_table = str.maketrans(english_digits, persian_digits)
    return str(text).translate(translation_table)


class PersianCalendarWidget(QTableWidget):
    """A widget to display a Persian calendar grid."""
    date_clicked = Signal(jdatetime.date)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRowCount(6)
        self.setColumnCount(7)
        self.setHorizontalHeaderLabels(["ش", "ی", "د", "س", "چ", "پ", "ج"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(38)
        self.horizontalHeader().setFixedHeight(40)
        self.setFixedSize(350, (40 + 6 * 38))

        # self.horizontalHeader().setFont(FontManager.get_font(size=11, bold=True))

        self.cellClicked.connect(self._on_cell_clicked)
        self.current_jdate = jdatetime.date.today()

        self._minimum_date = None

    def set_minimum_date(self, min_date: jdatetime.date):
        """Sets the minimum selectable date."""
        self._minimum_date = min_date
        self.populate()

    def set_date(self, year, month):
        """Sets the calendar to display the specified month and year."""
        self.current_jdate = jdatetime.date(year, month, 1)
        self.populate()

    def populate(self):
        """Populates the calendar grid with the correct days."""
        self.clearContents()
        first_day_of_month = self.current_jdate.replace(day=1)
        year, month = self.current_jdate.year, self.current_jdate.month

        if month <= 6:
            days_in_month = 31
        elif month <= 11:
            days_in_month = 30
        else:
            days_in_month = 30 if jdatetime.date.is_leap(year) else 29

        start_weekday = (first_day_of_month.weekday() + 1) % 7
        day = 1
        for row in range(6):
            for col in range(7):
                if (row == 0 and col < start_weekday) or day > days_in_month:
                    self.setItem(row, col, QTableWidgetItem(""))
                    continue

                item = QTableWidgetItem(to_persian_number(day))
                item.setTextAlignment(Qt.AlignCenter)
                current_day_obj = jdatetime.date(year, month, day)
                item.setData(Qt.ItemDataRole.UserRole, current_day_obj)

                # --- MODIFIED: Check against the minimum date ---
                if self._minimum_date and current_day_obj < self._minimum_date:
                    # Make the item look disabled
                    item.setForeground(QColor("lightgray"))
                    # Make the item non-selectable
                    item.setFlags(item.flags() & ~Qt.ItemIsSelectable)

                self.setItem(row, col, item)
                day += 1

    def _on_cell_clicked(self, row, column):
        item = self.item(row, column)
        if item and item.data(Qt.ItemDataRole.UserRole):
            self.date_clicked.emit(item.data(Qt.ItemDataRole.UserRole))

    def get_selected_date(self):
        selected_items = self.selectedItems()
        return selected_items[0].data(Qt.ItemDataRole.UserRole) if selected_items else None


class CalendarPopup(QWidget):
    """A popup widget containing a Persian calendar."""
    selection_made = Signal(object)

    def __init__(self, parent=None, year_range_past=0, year_range_future=0,
                 show_time_selector=False, minimum_datetime: jdatetime.datetime = None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup)
        self.setFocusPolicy(Qt.StrongFocus)
        # self.setFont(FontManager.get_font(size=11))

        self._minimum_datetime = minimum_datetime

        layout = QGridLayout(self)
        self.setLayout(layout)

        self.year_combo = QComboBox()
        self.month_combo = QComboBox()
        layout.addWidget(self.year_combo, 0, 1)
        layout.addWidget(self.month_combo, 0, 0)

        current_year = jdatetime.date.today().year
        years = range(current_year + year_range_future, current_year - year_range_past - 1, -1)
        for year in years:
            self.year_combo.addItem(to_persian_number(year), year)

        persian_months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
        for i, name in enumerate(persian_months, 1):
            self.month_combo.addItem(name, i)

        self.calendar = PersianCalendarWidget()
        if self._minimum_datetime:
            self.calendar.set_minimum_date(self._minimum_datetime.date())
        layout.addWidget(self.calendar, 1, 0, 1, 2)

        confirm_button = QPushButton("تایید")
        # confirm_button.setFont(FontManager.get_font(size=11, bold=True))
        layout.addWidget(confirm_button, 3, 0, 1, 2)

        # Connect signals for month/year updates
        self.year_combo.currentIndexChanged.connect(self.update_calendar)
        self.month_combo.currentIndexChanged.connect(self.update_calendar)

        # --- UX IMPROVEMENT: CONDITIONAL BEHAVIOR ---
        if show_time_selector:
            # Create and show the hour combo
            self.hour_combo = QComboBox()
            self.hour_combo.addItem("ساعت مشخص نشده", -1)
            for hour in range(8, 19):
                self.hour_combo.addItem(to_persian_number(f"{hour:02d}:00"), hour)
            layout.addWidget(self.hour_combo, 2, 0, 1, 2)

            # For InvoicePicker: A confirm button is required.
            # Clicking a date only highlights it.
            self.calendar.date_clicked.connect(self._update_time_selector_for_date)
            confirm_button.clicked.connect(self.emit_selection)
        else:
            # For BirthdayPicker/DataDatePicker: No confirm button needed.
            # Clicking a date immediately selects it and closes the popup.
            confirm_button.hide()
            self.calendar.date_clicked.connect(self.emit_selection)
        # --- END OF UX IMPROVEMENT ---

        today = jdatetime.date.today()
        self.year_combo.setCurrentText(to_persian_number(today.year))
        self.month_combo.setCurrentIndex(today.month - 1)
        self.update_calendar()

        if show_time_selector:
            # Highlight today by default
            today_item = self._find_item_by_date(today)
            if today_item:
                self.calendar.setCurrentItem(today_item)
            # Update the hour combo based on the current time
            self._update_time_selector_for_date(today)

    def update_calendar(self):
        year = self.year_combo.currentData()
        month = self.month_combo.currentData()
        if year and month:
            self.calendar.set_date(year, month)

    def emit_selection(self):
        selected_date = self.calendar.get_selected_date()
        if not selected_date:
            return

        if hasattr(self, "hour_combo") and self.hour_combo.currentData() != -1:
            hour = self.hour_combo.currentData()
            datetime_obj = jdatetime.datetime.combine(selected_date, jdatetime.time(hour, 0))
            self.selection_made.emit(datetime_obj)
        else:
            self.selection_made.emit(selected_date)
        self.close()

    def _update_time_selector_for_date(self, selected_date: jdatetime.date):
        if not hasattr(self, "hour_combo") or not self._minimum_datetime:
            return

        is_today = (selected_date == self._minimum_datetime.date())

        for i in range(self.hour_combo.count()):
            hour_data = self.hour_combo.itemData(i)
            if hour_data == -1: continue  # Skip "not specified"

            # If the selected date is today, disable past hours
            if is_today and hour_data < self._minimum_datetime.hour:
                self.hour_combo.model().item(i).setEnabled(False)
            # Otherwise (future date), ensure all hours are enabled
            else:
                self.hour_combo.model().item(i).setEnabled(True)

    def _find_item_by_date(self, date_to_find: jdatetime.date):
        for r in range(self.calendar.rowCount()):
            for c in range(self.calendar.columnCount()):
                item = self.calendar.item(r, c)
                if item and item.data(Qt.ItemDataRole.UserRole) == date_to_find:
                    return item
        return None


class DatePicker(QLineEdit):
    """A base class for date picker line edits."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("تاریخ را انتخاب کنید")
        self.setAlignment(Qt.AlignCenter)
        # self.setFont(FontManager.get_font(size=12))

    # --- FIX IS HERE: SCREEN-AWARE POSITIONING ---
    def mousePressEvent(self, event):
        if not hasattr(self, "popup"):
            return

        # Get screen geometry to ensure the popup stays within _view
        screen = self.screen()
        if not screen:
            screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()

        # Calculate initial popup position (below the line edit)
        pos = self.mapToGlobal(QPoint(0, self.height()))

        # Adjust horizontally if it goes off the right edge
        if pos.x() + self.popup.width() > screen_geometry.right():
            # Align popup's right edge with the line edit's right edge
            new_x = self.mapToGlobal(QPoint(self.width(), 0)).x() - self.popup.width()
            pos.setX(new_x)

        # Adjust vertically if it goes off the bottom edge
        if pos.y() + self.popup.height() > screen_geometry.bottom():
             # Position the popup *above* the line edit instead
            new_y = self.mapToGlobal(QPoint(0, 0)).y() - self.popup.height()
            pos.setY(new_y)

        self.popup.move(pos)
        self.popup.show()
        event.accept()
    # --- END OF FIX ---


class BirthdayPicker(DatePicker):
    """A date picker for selecting a birth date."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("تاریخ تولد را انتخاب کنید")
        self.popup = CalendarPopup(self, year_range_past=90)
        self.popup.selection_made.connect(self.set_date)
        self._selected_date = None

    def set_date(self, date_obj):
        if isinstance(date_obj, jdatetime.date):
            self._selected_date = date_obj
            self.setText(to_persian_number(date_obj.strftime("%Y/%m/%d")))

    def get_date(self):
        """
        Returns the selected date as a datetime.date (Gregorian).
        If no date is selected, returns None.
        """
        if self._selected_date is None:
            return None
        return self._selected_date.togregorian()


class InvoiceDatePicker(DatePicker):
    """A date picker for selecting an invoice delivery date and time."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("تاریخ و ساعت تحویل فاکتور را انتخاب کنید")

        self.popup = CalendarPopup(
            self,
            year_range_future=1,
            show_time_selector=True,
            minimum_datetime=jdatetime.datetime.now()
        )
        self.popup.selection_made.connect(self.set_date_or_datetime)

    def set_date_or_datetime(self, data_obj):
        """Handles both date and datetime objects from the popup."""
        if isinstance(data_obj, jdatetime.datetime):
            formatted_str = data_obj.strftime("%Y/%m/%d - %H:%M")
        elif isinstance(data_obj, jdatetime.date):
            formatted_str = data_obj.strftime("%Y/%m/%d")
        else:
            return
        self.setText(to_persian_number(formatted_str))


class DataDatePicker(DatePicker):
    """
    A date picker for selecting a date for data purposes.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("تاریخ مورد نظر را انتخاب کنید")
        self.popup = CalendarPopup(self, year_range_past=5, year_range_future=5)
        self.popup.selection_made.connect(self.set_date)
        self._selected_date = None

    def set_date(self, date_obj):
        """
        Sets the selected date. Expects a jdatetime.date object.
        """
        if isinstance(date_obj, jdatetime.date):
            self._selected_date = date_obj
            self.setText(to_persian_number(date_obj.strftime("%Y/%m/%d")))

    def get_date(self):
        """
        Returns the selected date as a datetime.date (Gregorian).
        If no date is selected, returns None.
        """
        if self._selected_date is None:
            return None
        return self._selected_date.togregorian()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # FontManager.load_fonts()

    main_window = QWidget()
    main_window.setWindowTitle("Date Picker Demo")
    # main_window.setFont(FontManager.get_font(size=12))

    layout = QVBoxLayout(main_window)
    layout.setSpacing(15)
    layout.setContentsMargins(15, 15, 15, 15)

    layout.addWidget(BirthdayPicker())
    layout.addWidget(InvoiceDatePicker())
    layout.addWidget(DataDatePicker())

    main_window.resize(400, 200)
    main_window.show()
    sys.exit(app.exec())
