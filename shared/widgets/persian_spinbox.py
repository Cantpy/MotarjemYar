from PySide6.QtWidgets import QSpinBox, QVBoxLayout, QLabel, QWidget
from PySide6.QtGui import QValidator
from PySide6.QtCore import Qt


class PersianSpinBox(QSpinBox):
    eastern_to_western = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
    western_to_persian = str.maketrans("0123456789,", "۰۱۲۳۴۵۶۷۸۹،")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignRight)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMaximum(999_999_999)
        self.setMinimum(0)
        self.setSingleStep(1000)
        self.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.setSuffix(" تومان")

    def valueFromText(self, text: str) -> int:
        # Normalize input: convert Persian to English digits, remove Persian/English commas
        cleaned = text.translate(self.eastern_to_western).replace("،", "").replace(",", "")
        try:
            return int(cleaned)
        except ValueError:
            return 0  # This value will be ignored unless validate() returns Acceptable

    def textFromValue(self, value: int) -> str:
        # Add commas and convert to Persian numerals and comma
        formatted = f"{value:,}"
        return formatted.translate(self.western_to_persian)

    def validate(self, text: str, pos: int):
        # Normalize to English digits
        cleaned = text.translate(self.eastern_to_western).replace("،", "").replace(",", "")
        if cleaned.isdigit():
            return QValidator.Acceptable, text, pos
        elif cleaned == "" or all(c in "۰۱۲۳۴۵۶۷۸۹،" for c in text):
            return QValidator.Intermediate, text, pos
        return QValidator.Invalid, text, pos

    def focusOutEvent(self, event):
        self.lineEdit().setText(self.textFromValue(self.value()))
        super().focusOutEvent(event)


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
