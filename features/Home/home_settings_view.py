from PySide6.QtWidgets import QDialog, QFormLayout, QSpinBox, QDialogButtonBox
from features.Home.models import Settings


class HomepageSettingsDialog(QDialog):
    def __init__(self, current_settings: Settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تنظیمات داشبورد")
        self.settings = current_settings
        self._init_ui()

    def _init_ui(self):
        layout = QFormLayout(self)

        self.row_spin = QSpinBox()
        self.row_spin.setValue(self.settings.row_count)

        self.days_spin = QSpinBox()
        self.days_spin.setValue(self.settings.threshold_days)

        self.orange_spin = QSpinBox()
        self.orange_spin.setValue(self.settings.orange_threshold_days)

        self.red_spin = QSpinBox()
        self.red_spin.setValue(self.settings.red_threshold_days)

        self.cards_spin = QSpinBox()
        self.cards_spin.setValue(self.settings.total_cards_number)

        layout.addRow("تعداد ردیف جدول", self.row_spin)
        layout.addRow("نمایش فاکتورهای تا چند روز پیش", self.days_spin)
        layout.addRow("آستانه نارنجی", self.orange_spin)
        layout.addRow("آستانه قرمز", self.red_spin)
        layout.addRow("تعداد کارت آمار", self.cards_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_updated_settings(self) -> Settings:
        return Settings(
            row_count=self.row_spin.value(),
            threshold_days=self.days_spin.value(),
            orange_threshold_days=self.orange_spin.value(),
            red_threshold_days=self.red_spin.value(),
            total_cards_number=self.cards_spin.value(),
            stat_cards=None  # Add support if needed
        )


def show_homepage_settings_dialog(current_settings: Settings, parent=None) -> Settings:
    dialog = HomepageSettingsDialog(current_settings, parent)
    if dialog.exec() == QDialog.Accepted:
        return dialog.get_updated_settings()
    return current_settings  # Return original settings if cancelled
