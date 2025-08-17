# validators.py
from PySide6.QtWidgets import QLineEdit, QLabel
from PySide6.QtGui import QValidator
from PySide6.QtCore import Qt, Signal

# Assume your existing validation functions are in a shared utils file
from shared.utils.validation_utils import validate_national_id, validate_legal_national_id
from shared.widgets.persian_tools import PERSIAN_TO_ENGLISH


# --- The Enhanced Validator ---
class PersianNIDValidator(QValidator):
    def validate(self, input_text: str, pos: int):
        normalized = input_text.translate(PERSIAN_TO_ENGLISH)

        # --- Rule 1: Check for fundamentally unrecoverable errors first ---

        # If it contains non-digits (and is not empty), it's always Invalid.
        if not normalized.isdigit() and normalized != "":
            return QValidator.Invalid, input_text, pos

        # If it's too long, it's always Invalid.
        if len(normalized) > 11:
            return QValidator.Invalid, input_text, pos

        # --- Rule 2: Check for perfectly "Acceptable" states ---

        # A 10-digit number is Acceptable ONLY if the checksum is valid.
        if len(normalized) == 10 and validate_national_id(normalized):
            return QValidator.Acceptable, input_text, pos

        # An 11-digit number is Acceptable ONLY if the checksum is valid.
        if len(normalized) == 11 and validate_legal_national_id(normalized):
            return QValidator.Acceptable, input_text, pos

        # --- Rule 3: If it's not Invalid and not Acceptable, it must be Intermediate ---
        # This covers all other cases:
        # - The user is typing (length < 10)
        # - The user has typed a 10-digit number with a wrong checksum
        return QValidator.Intermediate, input_text, pos


# --- The PersianNIDEdit class is UNCHANGED and already correct ---
# It will work perfectly with the new validator.
class PersianNIDEdit(QLineEdit):
    validation_changed = Signal(QValidator.State, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setValidator(PersianNIDValidator(self))
        self.setAlignment(Qt.AlignRight)
        self.setPlaceholderText("کد/شناسه ملی ۱۰ یا ۱۱ رقمی")
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, text: str):
        state, _, _ = self.validator().validate(text, 0)
        entity_type = 'none'
        if state == QValidator.Acceptable:
            normalized_len = len(text.translate(PERSIAN_TO_ENGLISH))
            if normalized_len == 10:
                entity_type = 'real'
            elif normalized_len == 11:
                entity_type = 'legal'
        self.validation_changed.emit(state, entity_type)

    def text(self) -> str:
        return super().text().translate(PERSIAN_TO_ENGLISH)

    def strip(self) -> str:
        return super().text().strip().translate(PERSIAN_TO_ENGLISH)
