# features/Main_Window/main_window_logic.py

from typing import Optional

from features.Main_Window.main_window_models import UserProfileDTO
from features.Login.login_window_repo import LoginRepository
from shared.session_provider import ManagedSessionProvider

from typing import TYPE_CHECKING

# Conditional import to avoid circular dependencies
if TYPE_CHECKING:
    from features.Login.login_window_repo import LoginRepository


class MainWindowLogic:
    """
    Handles business _logic for the main application window.
    """

    def __init__(self, users_engine: ManagedSessionProvider, repo: "LoginRepository"):
        self._users_session = users_engine
        self._repo = repo

    def get_user_profile_for_view(self, username: str) -> Optional[UserProfileDTO]:
        """
        Fetches user data from the _repository and builds the UserProfileDTO
        needed by the InvoiceWizardWidget.
        """
        with self._users_session() as session:
            # We can reuse the get_user_by_username method from the LoginRepository
            user = self._repo.get_user_by_username(session, username)
            if not user or not user.user_profile:
                return None

            # Build the DTO from the database models
            return UserProfileDTO(
                id=user.id,
                full_name=user.user_profile.full_name,
                role_fa=user.user_profile.role_fa,
                avatar_path=user.user_profile.avatar_path  # Assuming this exists in your model
            )

    def get_user_id_for_host(self, username: str):

        with self._users_session() as session:
            user = self._repo.get_user_by_username(session, username)

            if not user or not user.id:
                return None

            return user.id
