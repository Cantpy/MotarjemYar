from PySide6.QtWidgets import (QSpinBox, QVBoxLayout, QLabel, QWidget, QHeaderView, QLineEdit, QDoubleSpinBox,
                               QStyledItemDelegate)
from PySide6.QtGui import QValidator, QFont, QPainter, QColor
from PySide6.QtCore import Qt
import re
from shared.utils.validation_utils import validate_national_id

WESTERN_DIGITS = "0123456789.,"
PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹٬٫" # Note: Using Persian comma and decimal point

TO_WESTERN_TABLE = str.maketrans(PERSIAN_DIGITS, WESTERN_DIGITS)
TO_PERSIAN_TABLE = str.maketrans(WESTERN_DIGITS, PERSIAN_DIGITS)


class PersianNIDValidator(QValidator):
    def validate(self, input_text: str, pos: int):
        normalized = input_text.translate(TO_WESTERN_TABLE)

        if normalized == "":
            return QValidator.Intermediate, input_text, pos

        if not normalized.isdigit():
            return QValidator.Invalid, input_text, pos

        # Limit length to 10 digits
        if len(normalized) > 10:
            return QValidator.Invalid, input_text, pos

        # If 10 digits are complete, check validity
        if len(normalized) == 10:
            if validate_national_id(normalized):
                return QValidator.Acceptable, input_text, pos
            else:
                return QValidator.Invalid, input_text, pos

        # Otherwise still typing → Intermediate
        return QValidator.Intermediate, input_text, pos

    def fixup(self, input_text: str) -> str:
        return "".join(ch for ch in input_text.translate(TO_WESTERN_TABLE) if ch.isdigit())[:10]


class PersianNIDEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setValidator(PersianNIDValidator(self))
        self.setAlignment(Qt.AlignRight)
        self.setPlaceholderText("کد ملی ۱۰ رقمی")

    def text(self) -> str:
        return super().text().translate(TO_WESTERN_TABLE)

    def strip(self) -> str:
        return super().text().strip().translate(TO_WESTERN_TABLE)


class PhoneValidator(QValidator):
    def validate(self, input_text: str, pos: int):
        # Normalize Persian digits to English before checking
        normalized = input_text.translate(TO_WESTERN_TABLE)

        if normalized == "":
            return QValidator.Intermediate, input_text, pos

        # Allow: optional + at start, then digits only
        if re.fullmatch(r"\+?\d*", normalized):
            return QValidator.Acceptable, input_text, pos

        return QValidator.Invalid, input_text, pos

    def fixup(self, input_text: str) -> str:
        text = input_text.translate(TO_WESTERN_TABLE)
        if text.startswith("+"):
            return "+" + "".join(ch for ch in text[1:] if ch.isdigit())
        return "".join(ch for ch in text if ch.isdigit())


class PhoneLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setValidator(PhoneValidator(self))
        self.setPlaceholderText("Phone (e.g., +989123456789 or ۰۹۱۲۳۴۵۶۷۸۹)")
        self.setAlignment(Qt.AlignRight)

    def text(self) -> str:
        # Always return normalized English digits
        return super().text().translate(TO_WESTERN_TABLE)

    def strip(self) -> str:
        return super().text().strip().translate(TO_WESTERN_TABLE)


# ---------------- Email Validator ---------------- #
class EmailValidator(QValidator):
    # Only allow English letters, digits, ., -, _, and @
    EMAIL_ALLOWED = re.compile(r"^[A-Za-z0-9._\-@]*$")

    def validate(self, input_text: str, pos: int):
        if input_text == "":
            return QValidator.Intermediate, input_text, pos
        if self.EMAIL_ALLOWED.fullmatch(input_text):
            return QValidator.Acceptable, input_text, pos
        return QValidator.Invalid, input_text, pos

    def fixup(self, input_text: str) -> str:
        return "".join(ch for ch in input_text if self.EMAIL_ALLOWED.match(ch))


class EmailLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setValidator(EmailValidator(self))
        self.setPlaceholderText("example@email.com")

    def text(self) -> str:
        # Return as-is (only English allowed)
        return super().text().strip()


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

    def header_data(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Vertical:
            return str(section + 1).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
        return super().headerData(section, orientation, role)


class PersianSpinBoxMixin:
    """
    A mixin to provide robust Persian localization for QSpinBox and QDoubleSpinBox.
    It correctly handles group separators, suffixes, and user input.
    """
    def textFromValue(self, value):
        """
        Called by the spinbox to get the display text for a given number.
        1. Get the standard formatted text from the base class (e.g., "1,234.50 %").
        2. Translate the entire result to Persian.
        """
        # Let the original C++ implementation do the hard work of formatting
        standard_text = super().textFromValue(value)
        return standard_text.translate(TO_PERSIAN_TABLE)

    def valueFromText(self, text: str):
        """
        Called by the spinbox to parse the user's input text into a number.
        1. Translate the user's text to a standard Western format.
        2. Remove suffixes and group separators.
        3. Convert the cleaned text to a number (int or float).
        """
        # Convert all Persian characters (digits, comma, decimal) to Western
        western_text = text.translate(TO_WESTERN_TABLE)

        # Remove the suffix (e.g., " %" or " تومان") for clean parsing
        suffix = self.suffix()
        if suffix:
            western_text = western_text.replace(suffix, "").strip()

        # Remove the group separator (comma) that prevents conversion to a number
        cleaned_text = western_text.replace(",", "")

        # Handle the case of an empty string
        if not cleaned_text:
            return 0

        # Let the base class handle the final conversion (int or float)
        return super().valueFromText(cleaned_text)

    def validate(self, text: str, pos: int):
        """
        We DO NOT override validate(). The base QSpinBox validator is complex and
        works correctly with a proper valueFromText implementation. Overriding it
        is fragile and was the source of many of the original bugs. The spinbox
        will call valueFromText, and if that works, the input is considered valid.
        """
        return super().validate(text, pos)


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


class PlainSpinBox(QSpinBox):
    """A simple QSpinBox that accepts both English and Persian digits but has no formatting."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.setGroupSeparatorShown(False) # No commas
        self.setRange(0, 999_999_999)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def valueFromText(self, text: str) -> int:
        """Converts text (potentially with Persian digits) to a standard integer."""
        cleaned = text.strip().translate(TO_WESTERN_TABLE)
        if not cleaned:
            return 0
        try:
            return int(cleaned)
        except ValueError:
            return 0

    def validate(self, text: str, pos: int) -> QValidator.State:
        """Allow only English or Persian digits."""
        if all(c in "۰۱۲۳۴۵۶۷۸۹0123456789" for c in text.strip()):
            return QValidator.State.Acceptable
        if text == "":
            return QValidator.State.Intermediate
        return QValidator.State.Invalid

    # We no longer need textFromValue because we want the display to be plain.

class PlainDoubleSpinBox(QDoubleSpinBox):
    """A simple QDoubleSpinBox that accepts English/Persian digits for percentages."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.setGroupSeparatorShown(False)
        self.setDecimals(2)
        self.setRange(0.0, 100.0)
        self.setSingleStep(0.5)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def valueFromText(self, text: str) -> float:
        """Converts text (potentially with Persian digits) to a standard float."""
        cleaned = text.strip().replace("٪", "").translate(TO_WESTERN_TABLE)
        if not cleaned:
            return 0.0
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def validate(self, text: str, pos: int) -> QValidator.State:
        """Allow digits, one decimal point, and the percent sign."""
        # This is a bit more complex for floats, so we'll rely on the base validator
        # after converting the text to a parsable format.
        cleaned = text.strip().translate(TO_WESTERN_TABLE)
        return super().validate(cleaned, pos)


class PersianDoubleSpinBox(PersianSpinBoxMixin, QDoubleSpinBox):
    """A double spinbox for displaying Persian percentages."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.setGroupSeparatorShown(True)
        self.setDecimals(2)
        self.setRange(0.0, 100.0)
        self.setSingleStep(0.5)
        self.setSuffix(" ٪")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class NormalSpinBox(PersianSpinBoxMixin, QSpinBox):
    """A spinbox for displaying Persian currency amounts."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.setGroupSeparatorShown(True)
        self.setRange(0, 999_999_999)
        self.setSingleStep(1000)
        self.setSuffix(" تومان")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


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
