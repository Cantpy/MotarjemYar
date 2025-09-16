# features/Info_Page/info_page_factory.py

from features.Info_Page.info_page_view import InfoPageView
from features.Info_Page.info_page_controller import InfoPageController
from features.Info_Page.info_page_logic import InfoPageLogic
from features.Info_Page.info_page_repo import InfoPageRepository

from shared.session_provider import SessionProvider


class InfoPageFactory:
    """Factory class to create and wire the Info Page module components."""

    @staticmethod
    def create(session_provider: SessionProvider, parent=None) -> InfoPageController:
        """
        Creates and wires the complete Info Page module.

        This static method follows a clean architecture pattern to instantiate and
        connect the repository, logic, view, and controller for the info page.

        Args:
            session_provider: The application's session provider instance, which
                              is responsible for managing database sessions.
            parent (QWidget, optional): The parent widget for the view. Defaults to None.

        Returns:
            InfoPageController: The fully wired controller for the info page,
                                ready to be integrated into the application's
                                page manager.
        """
        # 1. Instantiate the stateless repository
        repo = InfoPageRepository()

        # 2. Instantiate the logic, injecting the repository and session provider
        logic = InfoPageLogic(repo, session_provider)

        # 3. Instantiate the view, making it a child of the parent if provided
        view = InfoPageView(parent)

        # 4. Instantiate the controller, injecting the view and logic
        controller = InfoPageController(view, logic)

        # 5. Load the initial data from the database into the view
        controller.load_initial_data()

        # 6. Return the fully constructed and initialized controller
        return controller


if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication
    from core.database_init import DatabaseInitializer
    from core.database_seeder import DatabaseSeeder
    from core.config import DATABASE_PATHS

    app = QApplication(sys.argv)

    # 1. Initialize databases
    initializer = DatabaseInitializer()
    session_provider = initializer.setup_file_databases(DATABASE_PATHS)

    # 2. Seed (optional – dev/test mode)
    seeder = DatabaseSeeder(session_provider)
    seeder.seed_initial_data()

    # 3. Use factory
    controller = InfoPageFactory.create(session_provider=session_provider)

    main_widget = controller.get_view()
    main_widget.show()

    sys.exit(app.exec())
