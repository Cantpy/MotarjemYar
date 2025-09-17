# features/Main_Window/main_window_logic.py

import json
from typing import Optional

# We need the DTO and the repository for data access
from features.Main_Window.main_window_models import UserProfileDTO
from features.Login.login_window_repo import LoginRepository
from shared.session_provider import SessionProvider

# We'll use the same shared function to find the settings file
from shared import return_resource

from typing import TYPE_CHECKING

# Conditional import to avoid circular dependencies
if TYPE_CHECKING:
    from features.Login.login_window_repo import LoginRepository


class MainWindowLogic:
    """
    Handles business _logic for the main application window.
    """

    def __init__(self, session_provider: SessionProvider, repo: "LoginRepository"):
        self.session_provider = session_provider
        self.repo = repo
        self.user_session = session_provider.users

    def get_user_profile_for_view(self, username: str) -> Optional[UserProfileDTO]:
        """
        Fetches user data from the repository and builds the UserProfileDTO
        needed by the InvoiceWizardWidget.
        """
        session = self.user_session()
        try:
            # We can reuse the get_user_by_username method from the LoginRepository
            user = self.repo.get_user_by_username(session, username)
            if not user or not user.user_profile:
                return None

            # Build the DTO from the database models
            return UserProfileDTO(
                id=user.id,
                full_name=user.user_profile.full_name,
                role_fa=user.user_profile.role_fa,
                avatar_path=user.user_profile.avatar_path  # Assuming this exists in your model
            )
        finally:
            session.close()

    def get_user_id_for_host(self, username: str):

        with self.user_session() as session:
            user = self.repo.get_user_by_username(session, username)

            if not user or not user.id:
                return None

            return user.id

    # def get_remembered_user_info(self) -> Optional[UserProfileDTO]:
    #     """
    #     Checks the login_settings.json file for a remembered user's info.
    #     This provides a quick way to display user info on startup without a full DB query,
    #     if the design allows it.
    #     """
    #     try:
    #         settings_path = return_resource("databases", "login_settings.json")
    #         with open(settings_path, 'r', encoding='utf-8') as f:
    #             settings = json.load(f)
    #
    #         # Check if remember_me is true and full_name exists
    #         if settings.get('remember_me') and settings.get('full_name'):
    #             # We can create a partial DTO. Role_fa might not be in the file.
    #             return UserProfileDTO(
    #                 id=None,
    #                 full_name=settings.get('full_name'),
    #                 role_fa=settings.get('role_fa', 'نقش نامشخص'),  # Provide a default
    #                 avatar_path=None  # This info is not typically stored in the json
    #             )
    #     except (FileNotFoundError, json.JSONDecodeError):
    #         return None
    #     return None
