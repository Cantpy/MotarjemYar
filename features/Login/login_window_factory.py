# features/Login/factory.py

from shared.session_provider import SessionProvider
from features.Login.login_window_view import LoginWidget
from features.Login.login_window_controller import LoginController
from features.Login.login_window_logic import LoginService
from features.Login.login_window_repo import LoginRepository
from features.Login.login_settings_repo import LoginSettingsRepository


class LoginWindowFactory:
    """
    Creates a fully configured and wired Login feature (MVC).
    """

    @staticmethod
    def create(session_provider: SessionProvider) -> LoginController:
        """
        Creates and wires the login window components.

        Args:
            session_provider: The central dependency container that provides
                              the necessary database session maker.

        Returns:
            The fully configured LoginController, which is the entry point
            to the login feature.
        """
        # 1. Instantiate the repositories
        login_repo = LoginRepository()
        settings_repo = LoginSettingsRepository()

        # 2. Instantiate the logic layer, injecting both repositories
        #    and the specific session maker it needs.
        logic = LoginService(
            repo=login_repo,
            settings_repo=settings_repo,
            user_session_factory=session_provider.users
        )

        # 3. Create the view and controller
        view = LoginWidget()
        controller = LoginController(view=view, logic=logic)

        return controller
