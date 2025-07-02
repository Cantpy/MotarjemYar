from PySide6.QtWidgets import QWidget, QComboBox, QLineEdit, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt, Signal, QPoint
import jdatetime
from .PersianCalendar import PersianCalendarWidget


class BirthdayPopup(QWidget):
    date_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup)
        self.setLayout(QVBoxLayout())
        self.setWindowTitle("انتخاب تاریخ تولد")

        # Year/Month Selectors (سال از امسال تا ۸۰ سال قبل)
        self.year_combo = QComboBox()
        self.month_combo = QComboBox()

        current_year = jdatetime.date.today().year
        for year in range(current_year, current_year - 81, -1):
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

        self.calendar = PersianCalendarWidget(disable_past_dates=False)  # اجازه انتخاب تاریخ گذشته
        self.layout().addWidget(self.calendar)

        # حذف ساعت
        # self.hour_combo = QComboBox()  <-- حذف شد

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
        self.date_selected.emit(date_str)
        self.hide()


class BirthdayPickerLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("تاریخ را انتخاب کنید")
        self.setReadOnly(True)

        self.calendar_popup = BirthdayPopup(self)
        self.calendar_popup.date_selected.connect(self.setText)
        self.calendar_popup.hide()

    def mousePressEvent(self, event):
        pos = self.mapToGlobal(QPoint(0, self.height()))
        self.calendar_popup.move(pos)
        self.calendar_popup.show()
        self.calendar_popup.raise_()
        event.accept()