from PySide6.QtWidgets import QWidget, QComboBox, QVBoxLayout, QPushButton, QLineEdit
from PySide6.QtCore import Qt, Signal, QPoint
import jdatetime
from .PersianCalendar import PersianCalendarWidget


class CalendarPopup(QWidget):
    date_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup)
        self.setLayout(QVBoxLayout())
        self.setWindowTitle("انتخاب تاریخ")

        # Year/Month Selectors
        self.year_combo = QComboBox()
        self.month_combo = QComboBox()
        current_year = jdatetime.date.today().year
        for year in range(current_year, current_year + 3):
            self.year_combo.addItem(str(year), year)

        persian_months = [
            "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
            "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
        ]
        for i, name in enumerate(persian_months, 1):
            self.month_combo.addItem(name, i)

        today = jdatetime.date.today()
        self.year_combo.setCurrentText(str(today.year))
        self.month_combo.setCurrentIndex(today.month - 1)

        self.layout().addWidget(self.year_combo)
        self.layout().addWidget(self.month_combo)

        self.calendar = PersianCalendarWidget()
        self.layout().addWidget(self.calendar)

        self.hour_combo = QComboBox()
        self.hour_combo.addItem("ساعت مشخص نشده است")
        for hour in range(8, 19):
            self.hour_combo.addItem(f"{hour:02d}:00")
        self.layout().addWidget(self.hour_combo)

        btn = QPushButton("تأیید")
        btn.clicked.connect(self.emit_date)
        self.layout().addWidget(btn)

        self.year_combo.currentIndexChanged.connect(self.update_calendar)
        self.month_combo.currentIndexChanged.connect(self.update_calendar)

    def update_calendar(self):
        self.calendar.set_month_and_year(
            self.year_combo.currentData(),
            self.month_combo.currentData()
        )

    def emit_date(self):
        selected_date = self.calendar.get_selected_date()
        if not selected_date:
            return

        date_str = f"{selected_date.year}/{selected_date.month:02d}/{selected_date.day:02d}"
        if self.hour_combo.currentText() != "ساعت مشخص نشده است":
            date_str += f" - {self.hour_combo.currentText()}"

        self.date_selected.emit(date_str)
        self.hide()


class DatePickerLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("تاریخ را انتخاب کنید")
        self.setReadOnly(True)

        self.calendar_popup = CalendarPopup(self)
        self.calendar_popup.date_selected.connect(self.setText)
        self.calendar_popup.hide()

    def mousePressEvent(self, event):
        pos = self.mapToGlobal(QPoint(0, self.height()))
        self.calendar_popup.move(pos)
        self.calendar_popup.show()
        self.calendar_popup.raise_()
        event.accept()