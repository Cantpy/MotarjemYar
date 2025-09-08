# home_page/factory.py

from sqlalchemy.orm import sessionmaker

from features.Home_Page.home_page_controller import HomePageController
from features.Home_Page.home_page_view import HomePageView
from features.Home_Page.home_page_settings.home_page_settings_repo import HomepageSettingsRepository
from features.Home_Page.home_page_settings.home_page_settings_logic import HomepageSettingsLogic
from features.Home_Page.home_page_logic import HomePageLogic
from features.Home_Page.home_page_repo import HomePageRepository
from shared.session_provider import SessionProvider


class HomePageFactory:
    """
    Factory for creating and wiring all components of the home page.
    It accepts pre-configured session makers.
    """

    @staticmethod
    def create(session_provider: SessionProvider, parent=None) -> HomePageController:
        """
        Creates a fully configured and connected home page module.

        Returns:
            HomePageController: The main controller which holds the view.
        """
        # 1. Create Data and Logic components
        repository = HomePageRepository()
        logic = HomePageLogic(
            repository=repository,
            session_provider=session_provider
        )

        # 2. Create the UI (View)
        view = HomePageView(parent=parent)

        # 3. Create the Settings Manager
        settings_repository = HomepageSettingsRepository()
        settings_manager = HomepageSettingsLogic(settings_repository)

        # 4. Create the Controller, injecting its dependencies
        controller = HomePageController(
            view=view,
            logic=logic,
            settings_manager=settings_manager
        )

        return controller
