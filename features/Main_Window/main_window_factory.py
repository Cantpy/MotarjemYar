# features/main_window/factory.py

from sqlalchemy.engine import Engine

from features.Main_Window.main_window_view import MainWindowView
from features.Main_Window.main_window_logic import MainWindowLogic
from features.Main_Window.main_window_controller import MainWindowController
from features.Login.login_window_repo import LoginRepository

from shared.session_provider import ManagedSessionProvider


class MainWindowFactory:
    """Creates a fully configured main window MVC stack."""

    @staticmethod
    def create(engines: dict[str, Engine], username: str) -> MainWindowController:
        """
        Creates and wires the main window components.

        Args:
            engines: The SQLAlchemy engine for the users database.
            username: The username of the logged-in user.

        Returns:
            The fully configured InvoiceWizardController.
        """
        users_engine = engines.get('users')
        if not users_engine:
            raise RuntimeError("MainWindowFactory requires the 'users' engine.")

        users_session = ManagedSessionProvider(engine=users_engine)
        repo = LoginRepository()
        logic = MainWindowLogic(repo=repo, users_engine=users_session)
        view = MainWindowView()

        controller = MainWindowController(view=view,
                                          logic=logic,
                                          username=username,
                                          engines=engines)

        return controller


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    # Use the generic test helper we designed
    from shared.testing.launch_feature import launch_feature_for_ui_test

    # --- THIS IS THE OLD, INCORRECT WAY ---
    # launch_feature_for_ui_test(
    #     factory_class=MainWindowFactory,
    #     required_engine_names={'customers', 'invoices'}, # This is now incomplete and wrong
    #     use_memory_db=True
    # )

    # --- THIS IS THE NEW, CORRECT WAY ---
    # The main window test is special and can't use the simple helper.
    # It needs to be a mini-version of your ApplicationManager's startup.

    app = QApplication(sys.argv)

    # 1. We need ALL the engines for the MainWindow
    from core.database_init import DatabaseInitializer

    initializer = DatabaseInitializer()
    all_engines = initializer.setup_memory_databases()

    # 2. We need a dummy username
    username_for_test = "testuser"

    # 3. Call the factory with the correct, full dictionary of engines
    controller = MainWindowFactory.create(
        engines=all_engines,
        username=username_for_test
    )

    # 4. Show the view
    main_widget = controller.get_view()
    main_widget.show()

    sys.exit(app.exec())
