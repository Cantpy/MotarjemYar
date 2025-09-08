# features/Pome_Page/home_page_settings/home_page_settings_factory.py

from features.Home_Page.home_page_settings.home_page_settings_repo import HomepageSettingsRepository
from features.Home_Page.home_page_settings.home_page_settings_logic import HomepageSettingsLogic
from features.Home_Page.home_page_settings.home_page_settings_controller import HomepageSettingsController


class HomepageSettingsFactory:
    @staticmethod
    def create() -> HomepageSettingsController:
        """Creates a fully wired settings management component."""
        repository = HomepageSettingsRepository()
        logic = HomepageSettingsLogic(repository)
        controller = HomepageSettingsController(logic)
        return controller
