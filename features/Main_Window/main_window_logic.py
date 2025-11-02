# features/Main_Window/main_window_logic.py

from typing import Optional

from features.Main_Window.main_window_models import UserProfileDTO
from features.Login.login_window_repo import LoginRepository
from shared.session_provider import ManagedSessionProvider

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from features.Login.login_window_repo import LoginRepository


class MainWindowLogic:
    """
    Handles business _logic for the main application window.
    """

    def __init__(self, users_engine: ManagedSessionProvider, repo: "LoginRepository"):
        self._users_session = users_engine
        self._repo = repo

    def _translate_role_to_farsi(self, role: str) -> str:
        translations = {
            "admin": "مدیر سیستم",
            "translator": "مترجم",
            "clerk": "کارمند دفتری",
            "accountant": "حسابدار",
        }
        return translations.get(role, "کاربر")

    def get_user_profile_for_view(self, username: str) -> Optional[UserProfileDTO]:
        """
        Fetches user data directly from the UsersModel and builds a UserProfileDTO
        for UI components like InvoiceWizardWidget.
        """
        with self._users_session() as session:
            user = self._repo.get_user_by_username(session, username)
            if not user:
                return None

            return UserProfileDTO(
                id=user.id,
                full_name=user.display_name,
                role_fa=self._translate_role_to_farsi(user.role),
                avatar_path=user.avatar_path if hasattr(user, "avatar_path") else None,
            )

    def get_user_id_for_host(self, username: str):

        with self._users_session() as session:
            user = self._repo.get_user_by_username(session, username)

            if not user or not user.id:
                return None

            return user.id
