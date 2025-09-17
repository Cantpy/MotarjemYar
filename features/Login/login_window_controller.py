# controller.py
from PySide6.QtCore import QTimer, QObject, Signal, Slot
from features.Login.login_window_view import LoginWidget
from features.Login.login_window_logic import LoginService
from features.Login.login_window_models import UserLoginDTO

from shared import show_error_message_box, show_information_message_box, show_warning_message_box
from shared.utils.login_utils import get_persian_role_text


class LoginController(QObject):
    """
    Controller for the login window, mediating between the _view and the service layer.
    """
    login_successful = Signal(str, str)

    def __init__(self, view: LoginWidget, logic: LoginService):
        super().__init__()
        self._view = view
        self._logic = logic
        self._connect_signals()
        self._check_for_remembered_login_on_startup()

    def get_view(self):
        return self._view

    def _connect_signals(self):
        """Connects the _view's action signals to the controller's handlers."""
        self._view.login_attempted.connect(self._handle_login_request)
        self._view.password_visibility_toggled.connect(self._handle_password_toggle)
        self._view.reset_form_requested.connect(self._handle_reset_form_request)

    # Handler methods for View's signals (these are the 'slots' for user actions)
    def _handle_login_request(self, username: str, password: str, remember_me: bool):
        """Receives the login request and passes it to the _logic layer."""
        if not username or not password:
            show_warning_message_box(self._view, "خطا", "لطفاً نام کاربری و رمز عبور را وارد کنید.")
            return

        self._view.disable_login_button("در حال بررسی...")
        QTimer.singleShot(100, lambda: self._perform_authentication(username, password, remember_me))

    def _perform_authentication(self, username: str, password: str, remember_me: bool):
        """
        Creates the DTO and calls the single, powerful _logic method.
        """
        login_dto = UserLoginDTO(username=username, password=password, remember_me=remember_me)
        success, message, user_dto = self._logic.login(login_dto)

        if success and user_dto:
            role_text = get_persian_role_text(user_dto.role, user_dto.role_fa)
            self._view.login_successful_ui(user_dto.full_name, role_text)
            self.login_successful.emit(user_dto.username, user_dto.role)
        else:
            self._view.login_failed_ui(message)
            show_error_message_box(self._view, "خطا", message)

        self._view.enable_login_button("ورود")

    def _check_for_remembered_login_on_startup(self):
        """Initiates the check for auto-login."""
        success, user_dto = self._logic.check_and_auto_login()
        if success and user_dto:
            role_text = get_persian_role_text(user_dto.role, user_dto.role_fa)
            self._view.set_remember_me_checkbox(True)
            self._view.login_successful_ui(user_dto.full_name, role_text)
            self.login_successful.emit(user_dto.username, user_dto.role)
        else:
            self._view.reset_form_ui()

    @Slot(int)
    def _handle_password_toggle(self, current_echo_mode: int) -> None:
        """
        Receives the toggle request from the _view and instructs the _view
        on how to update its UI state.
        """
        # The controller's _logic is simple: tell the _view to do the UI work.
        self._view.toggle_password_visibility_ui(current_echo_mode)

    def _handle_reset_form_request(self) -> None:
        """
        Handles the user's request to log out and reset the form.
        This is now much simpler.
        """
        # The controller doesn't need to know the username. It asks the _view.
        # This makes the controller stateless.
        username_in_field = self._view.username_input.text().strip()

        # Make a single, high-level call to the _logic layer.
        self._logic.logout(username_in_field)

        # Tell the _view to update its UI.
        self._view.reset_form_ui()
