# features/home_page/settings/controller.py
from PySide6.QtCore import QObject, Slot
from features.Home_Page.home_page_settings.home_page_settings_logic import HomepageSettingsLogic
from features.Home_Page.home_page_settings.home_page_settings_view import HomepageSettingsDialog
from features.Home_Page.home_page_settings.home_page_settings_models import Settings
from shared import show_warning_message_box


class HomepageSettingsController(QObject):
    def __init__(self, logic: HomepageSettingsLogic):
        super().__init__()
        self._logic = logic
        self._dialog = None

    def show_dialog(self, parent=None):
        """Creates, shows, and manages the settings dialog."""
        current_settings = self._logic.get_current_settings()
        self._dialog = HomepageSettingsDialog(current_settings, parent)
        self._dialog.save_requested.connect(self._on_save_requested)
        self._dialog.exec()

    @Slot(Settings)
    def _on_save_requested(self, updated_settings: Settings):
        """Handles the user's request to save new settings."""
        errors = self._logic.validate_settings(updated_settings)
        if errors:
            message = "خطا در تنظیمات:\n" + "\n".join(errors)
            show_warning_message_box(self._dialog, "خطای اعتبارسنجی", message)
            return  # Keep dialog open for user to fix

        # If validation passes, tell logic to save
        self._logic.save_settings(updated_settings)
        self._dialog.accept()     # Close the dialog
