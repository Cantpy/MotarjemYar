# features/main_window/factory.py
from shared.session_provider import SessionProvider
from features.Main_Window.main_window_view import MainWindowView
from features.Main_Window.main_window_logic import MainWindowLogic
from features.Main_Window.main_window_controller import MainWindowController
from features.Login.login_window_repo import LoginRepository


class MainWindowFactory:
    """Creates a fully configured main window MVC stack."""

    @staticmethod
    def create(session_provider: SessionProvider) -> MainWindowController:
        """
        Creates and wires the main window components.

        Args:
            session_provider: The central dependency container for database sessions.

        Returns:
            The fully configured InvoiceWizardController.
        """
        # The logic layer holds the session provider to pass down to sub-features.
        login_repository = LoginRepository()
        logic = MainWindowLogic(session_provider, login_repository)
        view = MainWindowView()  # The QMainWindow widget
        controller = MainWindowController(view=view, logic=logic)

        return controller
