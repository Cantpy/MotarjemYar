# features/Login/login_window_logic.py

import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError

from features.Login.login_window_repo import LoginRepository
from features.Login.auth_file_repo import AuthFileRepository
from shared.dtos.auth_dtos import RememberSettingsDTO, UserLoginDTO, LoggedInUserDTO, SessionDataDTO
from shared.session_provider import ManagedSessionProvider


class LoginService:
    """
    The refactored _logic layer for the login feature.
    """
    def __init__(self, repo: LoginRepository,
                 auth_file_repo: AuthFileRepository,
                 user_engine: ManagedSessionProvider):
        self.repo = repo
        self.auth_file_repo = auth_file_repo
        self._users_session = user_engine

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
            self.auth_file_repo.clear_remember_me()

    def authenticate_user(self, login_dto: UserLoginDTO) -> tuple[bool, str, Optional[LoggedInUserDTO]]:
        """
        Authenticates a user, now with spam protection and lockout logic.
        """
        with self._users_session() as session:
            try:
                user = self.repo.get_user_by_username(session, login_dto.username)

                # --- STEP 1: Check for existing user ---
                if not user:
                    return False, "نام کاربری یا رمز عبور اشتباه است.", None

                # --- STEP 2: Check if account is currently locked ---
                if user.lockout_until_utc and user.lockout_until_utc > datetime.utcnow():
                    time_remaining = user.lockout_until_utc - datetime.utcnow()
                    minutes_left = round(time_remaining.total_seconds() / 60)
                    message = (f"حساب کاربری به دلیل تلاش‌های ناموفق متعدد قفل شده است."
                               f" لطفاً بعد از {minutes_left} دقیقه دوباره امتحان کنید.")
                    return False, message, None

                # --- STEP 3: Check if user is active ---
                if user.active == 0:
                    return False, "حساب کاربری غیرفعال است.", None

                # --- STEP 4: Verify the password ---
                password_is_valid = bcrypt.checkpw(login_dto.password.encode('utf-8'), user.password_hash)

                if password_is_valid:
                    # --- SUCCESS PATH ---
                    # If the user had previous failed attempts, reset them.
                    self.repo.reset_login_attempts(session, user)
                    session.commit()

                    # Build and return the successful user DTO
                    profile = user.user_profile
                    logged_in_user = LoggedInUserDTO(
                        username=user.username,
                        role=user.role,
                        role_fa=profile.role_fa if profile else None,
                        full_name=profile.full_name if profile else None
                    )
                    return True, "ورود موفق!", logged_in_user
                else:
                    # --- FAILURE PATH ---
                    # Record the failed attempt in the database.
                    self.repo.record_failed_login(session, user)
                    session.commit()

                    # Return the generic error message. Do not reveal how many attempts are left.
                    return False, "نام کاربری یا رمز عبور اشتباه است.", None

            except (SQLAlchemyError, ValueError) as e:
                session.rollback()
                print(f"Authentication Error: {e}")
                return False, "خطا در فرآیند احراز هویت.", None

    def check_and_auto_login(self) -> tuple[bool, Optional[LoggedInUserDTO]]:
        """Checks for and performs auto-login."""
        # REFACTORED: Uses the settings _repository
        settings = self.auth_file_repo.load_remember_me()
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
        self.auth_file_repo.clear_remember_me()
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
        self.auth_file_repo.save_remember_me(settings_dto)

    def _clear_remember_me(self, username: str):
        """Clears remember-me tokens from the DB and the settings file."""
        with self._users_session() as session:
            self.repo.update_user_token(session, username, None, None)
            session.commit()
        self.auth_file_repo.clear_remember_me()

    def start_session(self, user_dto: LoggedInUserDTO) -> None:
        """
        Orchestrates all actions needed for a successful login session start:
        1. Create a log entry in the database.
        2. Create the current_session.json file.
        """
        print(f"--- Starting session for user: {user_dto.username} ---")
        login_time = datetime.now()

        with self._users_session() as session:
            try:
                # Get the full user object to access its ID
                user = self.repo.get_user_by_username(session, user_dto.username)
                if not user:
                    print("Error: Could not find user to start session.")
                    return

                # 1. Create the DB log entry
                log_entry = self.repo.create_login_log_entry(session, user.id, login_time)
                session.commit()

                # 2. Create the DTO for the session file
                session_dto = SessionDataDTO(
                    user_id=user.id,
                    username=user.username,
                    role=user.role,
                    full_name=user_dto.full_name,
                    role_fa=user_dto.role_fa,
                    login_time=login_time.isoformat(),
                    log_id=log_entry.id  # <-- Store the log ID
                )

                # 3. Create the session file using its repository
                self.auth_file_repo.save_session(session_dto)
                print("--- Session started successfully. ---")

            except Exception as e:
                print(f"Error starting session: {e}")
                session.rollback()

    def end_session(self) -> None:
        """
        Orchestrates all actions for a graceful session end:
        1. Load the session file to find out who is logged in.
        2. Update the corresponding log entry in the database with a logout time.
        3. Delete the session file.
        """
        print("--- Ending session... ---")
        # 1. Find out who is logged in by loading the session file
        session_data = self.auth_file_repo.load_session()
        if not session_data:
            print("No active session file found to end.")
            return

        logout_time = datetime.now()

        # 2. Update the DB log entry
        with self._users_session() as session:
            try:
                self.repo.update_logout_time(session, session_data.log_id, logout_time)
                session.commit()
                print(f"Logout time recorded for user: {session_data.username}")
            except Exception as e:
                print(f"Error recording logout time: {e}")
                session.rollback()

        # 3. Delete the session file
        self.auth_file_repo.clear_session()
        print("--- Session ended successfully. ---")