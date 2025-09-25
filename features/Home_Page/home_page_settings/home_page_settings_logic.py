# features/home_page/settings/_logic.py
from typing import Optional, List
from PySide6.QtCore import QObject, Signal
from features.Home_Page.home_page_settings.home_page_settings_models import Settings
from features.Home_Page.home_page_settings.home_page_settings_repo import HomepageSettingsRepository


class HomepageSettingsLogic(QObject):
    """
    Manages the state of the homepage settings.
    Orchestrates loading from and saving to the _repository.
    """
    settings_changed = Signal(Settings)

    def __init__(self, repository: HomepageSettingsRepository, max_cards: int = 6):
        super().__init__()
        self._repository = repository
        self._max_cards = max_cards
        self.current_settings = self._load_or_default()

    def get_current_settings(self) -> Settings:
        return self.current_settings

    def _load_or_default(self) -> Settings:
        settings = self._repository.load()
        if settings:
            return settings
        return Settings.default(self._max_cards)

    def save_settings(self, settings: Settings) -> bool:
        """Saves the provided settings via the _repository."""
        success = self._repository.save(settings)
        if success:
            self.current_settings = settings
            self.settings_changed.emit(self.current_settings)
        return success

    def reset_to_defaults(self):
        """Resets settings to default values and saves them."""
        defaults = Settings.default(self._max_cards)
        self.save_settings(defaults)

    def validate_settings(self, settings: Settings) -> List[str]:
        """Applies business rules to validate settings."""
        errors = []
        enabled_count = len(settings.get_enabled_cards())

        if enabled_count % 3 != 0:
            errors.append("تعداد کارت‌های انتخاب شده باید مضرب ۳ باشد.")
        if settings.red_threshold_days >= settings.orange_threshold_days:
            errors.append("آستانه قرمز باید کمتر از آستانه نارنجی باشد.")
        if settings.orange_threshold_days >= settings.threshold_days:
            errors.append("آستانه نارنجی باید کمتر از حد آستانه کلی باشد")
        # ... other validation rules ...
        return errors
