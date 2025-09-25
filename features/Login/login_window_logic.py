# features/Login/login_window_logic.py

import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError

from features.Login.login_window_repo import LoginRepository
from features.Login.login_settings_repo import LoginSettingsRepository
from shared.dtos.auth_dtos import RememberSettingsDTO, UserLoginDTO, LoggedInUserDTO
from shared.session_provider import ManagedSessionProvider


class LoginService:
    """
    The refactored _logic layer for the login feature.
    """
    def __init__(self, repo: LoginRepository, settings_repo: LoginSettingsRepository,
                 session_provider: ManagedSessionProvider):
        self.repo = repo
        self.settings_repo = settings_repo
        self._users_session = session_provider

    def login(self, login_dto: UserLoginDTO) -> tuple[bool, str, Optional[LoggedInUserDTO]]:
        """
        A single, powerful method to handle the entire login process.
        It authenticates and then handles the 'remember me' _logic internally.
        """
        # Step 1: Authenticate the user.
        success, message, user_dto = self.authenticate_user(login_dto)
        if not success:
            return False, message, None

        # Step 2: If authentication is successful, handle the 'remember me' _logic.
        # This is the business rule: "On successful login, update the remember me state."
        if login_dto.remember_me:
            self._setup_remember_me(login_dto.username)
        else:
            self._clear_remember_me(login_dto.username)

        user_dto.is_remembered = login_dto.remember_me
        return True, message, user_dto

    def logout(self, username: Optional[str]):
        """
        Logs a user out by clearing any 'remember me' tokens.
        """
        if username:
            self._clear_remember_me(username)
        else:
            # If there's no user, just make sure the file is gone.
            self.settings_repo.clear()

    def authenticate_user(self, login_dto: UserLoginDTO) -> tuple[bool, str, Optional[LoggedInUserDTO]]:
        """Authenticates a user based on provided credentials."""
        # REFACTORED: Simplified session management
        with self._users_session() as session:
            try:
                user = self.repo.get_user_by_username(session, login_dto.username)

                if not user or user.active == 0:
                    return False, "نام کاربری یا رمز عبور اشتباه است.", None

                if not bcrypt.checkpw(login_dto.password.encode('utf-8'), user.password_hash):
                    return False, "نام کاربری یا رمز عبور اشتباه است.", None

                # If authentication is successful, build the DTO
                profile = user.user_profile
                logged_in_user = LoggedInUserDTO(
                    username=user.username,
                    role=user.role,
                    role_fa=profile.role_fa if profile else None,
                    full_name=profile.full_name if profile else None
                )
                return True, "ورود موفق!", logged_in_user

            except (SQLAlchemyError, ValueError) as e:
                # Catch specific, expected errors
                print(f"Authentication Error: {e}")
                return False, "خطا در فرآیند احراز هویت.", None

    def check_and_auto_login(self) -> tuple[bool, Optional[LoggedInUserDTO]]:
        """Checks for and performs auto-login."""
        # REFACTORED: Uses the settings _repository
        settings = self.settings_repo.load()
        if not (settings and settings.remember_me and settings.username and settings.token):
            return False, None

        if self._verify_remember_token(settings.username, settings.token):
            # If token is valid, get the full user DTO
            with self._users_session() as session:
                user = self.repo.get_user_by_username(session, settings.username)
                if user and user.active == 1:
                    profile = user.user_profile
                    return True, LoggedInUserDTO(
                        username=user.username, role=user.role,
                        role_fa=profile.role_fa if profile else None,
                        full_name=profile.full_name if profile else None,
                        is_remembered=True
                    )

        # If we reach here, auto-login failed. Clear the invalid settings.
        self.settings_repo.clear()
        return False, None

    def _verify_remember_token(self, username: str, token: str) -> bool:
        """Verifies the remember me token against the database."""
        with self._users_session() as session:
            user = self.repo.get_user_by_username(session, username)
            if not (user and user.token_hash and user.expires_at):
                return False

            expires_dt = datetime.fromisoformat(user.expires_at)
            if datetime.now() >= expires_dt:
                return False

            return bcrypt.checkpw(token.encode('utf-8'), user.token_hash)

    def _setup_remember_me(self, username: str):
        """Generates and saves a remember-me token to the DB and settings file."""
        token = secrets.token_urlsafe(32)
        token_hash = bcrypt.hashpw(token.encode('utf-8'), bcrypt.gensalt())
        expires_at = (datetime.now() + timedelta(days=30)).isoformat()

        # Orchestrate the two save operations
        with self._users_session() as session:
            self.repo.update_user_token(session, username, token_hash, expires_at)
            session.commit()

            user = self.repo.get_user_by_username(session, username)
            full_name = user.user_profile.full_name if user.user_profile else ""

        settings_dto = RememberSettingsDTO(
            remember_me=True, username=username, token=token, full_name=full_name
        )
        self.settings_repo.save(settings_dto)

    def _clear_remember_me(self, username: str):
        """Clears remember-me tokens from the DB and the settings file."""
        with self._users_session() as session:
            self.repo.update_user_token(session, username, None, None)
            session.commit()
        self.settings_repo.clear()
