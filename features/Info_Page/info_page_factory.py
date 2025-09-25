# features/Info_Page/info_page_factory.py

from sqlalchemy.engine import Engine

from features.Info_Page.info_page_view import InfoPageView
from features.Info_Page.info_page_controller import InfoPageController
from features.Info_Page.info_page_logic import InfoPageLogic
from features.Info_Page.info_page_repo import InfoPageRepository

from shared.session_provider import ManagedSessionProvider


class InfoPageFactory:
    """
    Factory class to create and wire the Info Page module components.
    """
    @staticmethod
    def create(info_page_engine: Engine, parent=None) -> InfoPageController:
        """
        Creates and wires the complete Info Page module.

        This static method follows a clean architecture pattern to instantiate and
        connect the _repository, _logic, _view, and controller for the info page.

        Args:
            info_page_engine: The SQLAlchemy engine for the info page database.
            parent (QWidget, optional): The parent widget for the _view. Defaults to None.

        Returns:
            InfoPageController: The fully wired controller for the info page,
                                ready to be integrated into the application's
                                page manager.
        """
        info_page_session = ManagedSessionProvider(engine=info_page_engine)
        repo = InfoPageRepository()
        logic = InfoPageLogic(repo, info_page_session)
        view = InfoPageView(parent)
        controller = InfoPageController(view, logic)
        controller.load_initial_data()

        return controller


if __name__ == '__main__':
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=InfoPageFactory,
        required_engines={'info_page': 'info_page_engine'},
        use_memory_db=True
    )
