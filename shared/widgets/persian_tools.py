from PySide6.QtWidgets import (QSpinBox, QVBoxLayout, QLabel, QWidget, QHeaderView, QStyleOptionHeader, QStyle,
                               QStyledItemDelegate)
from PySide6.QtGui import QValidator, QFont, QPainter, QColor
from PySide6.QtCore import Qt, QRect


class PersianHeaderDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.western_to_persian = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
        self.font = QFont("Tahoma", 10, QFont.Bold)
        self.color = QColor(64, 64, 64)  # Dark gray

    def paint(self, painter: QPainter, option, index):
        # Persian numeral for the row index
        persian_text = str(index.row() + 1).translate(self.western_to_persian)

        painter.save()
        painter.setFont(self.font)
        painter.setPen(self.color)
        painter.drawText(option.rect, Qt.AlignCenter, persian_text)
        painter.restore()



class PersianVerticalHeader(QHeaderView):
    def __init__(self, parent=None):
        super().__init__(Qt.Vertical, parent)
        self.setFont(QFont("Tahoma", 10, QFont.Bold))
        self.western_to_persian = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Vertical:
            return str(section + 1).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
        return super().headerData(section, orientation, role)


class PersianSpinBox(QSpinBox):
    eastern_to_western = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
    western_to_persian = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

    def __init__(self, parent=None, suffix=""):
        super().__init__(parent)
        self.setFont(QFont("Tahoma", 10))
        self.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.setRange(0, 999_999_999)
        self.setGroupSeparatorShown(True)
        # Suffix is now passed in constructor for flexibility
        if suffix:
            self.setSuffix(f" {suffix}")

    def textFromValue(self, value: int) -> str:
        return str(value).translate(self.western_to_persian)

    def valueFromText(self, text: str) -> int:
        # Remove suffix before processing
        suffix = self.suffix()
        if suffix:
            text = text.removesuffix(suffix)

        cleaned = text.strip().translate(self.eastern_to_western)
        try:
            return int(cleaned)
        except (ValueError, TypeError):
            return 0

    def validate(self, text: str, pos: int):
        # Allow only Persian digits
        suffix = self.suffix()
        if suffix:
            text = text.removesuffix(suffix)

        if all(c in "۰۱۲۳۴۵۶۷۸۹" for c in text.strip()):
            return QValidator.Acceptable, text, pos
        if text == "":
            return QValidator.Intermediate, text, pos
        return QValidator.Invalid, text, pos

    def show_error(self, message):
        """Highlight input field with red border and display error message below it."""
        self.setStyleSheet("border: 2px solid red; border-radius: 4px;")

        # Check if the error label already exists, if not, create it
        if not hasattr(self, "error_label"):
            self.error_label = QLabel(self.parent())
            self.error_label.setStyleSheet("color: red; font-size: 11px;")
            self.error_label.setWordWrap(True)

        self.error_label.setText(message)
        self.error_label.setGeometry(self.x(), self.y() + self.height() + 2, self.width(), 20)
        self.error_label.show()

    def clear_error(self):
        """Clear error styling and message from a line edit field."""
        self.setStyleSheet("")  # Clear red border
        if hasattr(self, "error_label"):
            self.error_label.hide()


class NormalSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignRight)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMaximum(999_999_999)
        self.setMinimum(0)
        self.setSingleStep(1000)
        self.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.setSuffix(" تومان")

    def textFromValue(self, value: int) -> str:
        # Just override the display, not parsing or validation
        formatted = f"{value:,}"
        return formatted.translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


class PriceInputWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.input = QSpinBox()
        self.input.setMaximum(999_999_999)
        self.input.setSingleStep(1000)
        self.input.setAlignment(Qt.AlignRight)
        self.input.setLayoutDirection(Qt.RightToLeft)

        self.input_label = QLabel("۰ تومان")
        self.input_label.setAlignment(Qt.AlignRight)

        layout = QVBoxLayout()
        layout.addWidget(self.input)
        layout.addWidget(self.input_label)
        self.setLayout(layout)

        self.input.valueChanged.connect(self.update_label)

    def update_label(self, value):
        formatted = f"{value:,}"
        persian = formatted.translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
        self.input_label.setText(f"{persian} تومان")
