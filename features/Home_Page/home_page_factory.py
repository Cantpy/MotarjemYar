# home_page/factory.py

from sqlalchemy.engine import Engine

from features.Home_Page.home_page_controller import HomePageController
from features.Home_Page.home_page_view import HomePageView
from features.Home_Page.home_page_logic import HomePageLogic
from features.Home_Page.home_page_repo import HomePageRepository

from shared.session_provider import ManagedSessionProvider


class HomePageFactory:
    """
    Factory for creating and wiring all components of the home page.
    It accepts pre-configured session makers.
    """

    @staticmethod
    def create(business_engine: Engine, parent=None) -> HomePageController:
        """
        Creates a fully configured Home Page module.

        Args:
            business_engine: The SQLAlchemy engine for the business database.
            parent: The parent widget.

        Returns:
            HomePageController: The main controller which holds the view.
        """

        business_session = ManagedSessionProvider(engine=business_engine)

        # 1. Create Data and Logic components
        repository = HomePageRepository()
        logic = HomePageLogic(
            repository=repository,
            business_engine=business_session
        )

        # 2. Create the UI (View)
        view = HomePageView(parent=parent)

        # 4. Create the Controller, injecting its dependencies
        controller = HomePageController(
            view=view,
            logic=logic
        )

        return controller


if __name__ == "__main__":
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=HomePageFactory,
        required_engines={'business': 'business'},
        use_memory_db=True
    )
