# features/Login/factory.py

from sqlalchemy import Engine

from features.Login.login_window_view import LoginWidget
from features.Login.login_window_controller import LoginController
from features.Login.login_window_logic import LoginService
from features.Login.login_window_repo import LoginRepository
from features.Login.auth_file_repo import AuthFileRepository

from shared.session_provider import ManagedSessionProvider


class LoginWindowFactory:
    """
    Creates a fully configured and wired Login feature (MVC).
    """

    @staticmethod
    def create(engine: Engine) -> LoginController:
        """
        Creates and wires the login window components.

        Args:
            engine: The central dependency container that provides the necessary database session maker.

        Returns:
            The fully configured LoginController, which is the entry point to the login feature.
        """
        user_engine = ManagedSessionProvider(engine=engine)

        login_repo = LoginRepository()
        auth_file_repo = AuthFileRepository()

        logic = LoginService(
            repo=login_repo,
            auth_file_repo=auth_file_repo,
            user_engine=user_engine
            )

        view = LoginWidget()
        controller = LoginController(view=view, logic=logic)

        return controller


if __name__ == '__main__':
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=LoginWindowFactory,
        required_engines={'users': 'users_engine'},
        use_memory_db=True
    )
