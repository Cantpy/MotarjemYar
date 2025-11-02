# features/Login/login_window_repo.py

from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload, Session
from sqlalchemy.exc import SQLAlchemyError

from config.config import MAX_LOGIN_ATTEMPTS, LOCKOUT_DURATION_MINUTES
from shared.orm_models.users_models import UsersModel, LoginLogsModel


class LoginRepository:
    """
    Repository for user authentication and management.
    """
    def get_user_by_username(self, session, username: str) -> UsersModel | None:
        """
        Fetch a user by username, optionally eager-loading related data
        like login logs and security questions.
        """
        try:
            user = (
                session.query(UsersModel)
                .options(
                    joinedload(UsersModel.login_logs),
                    joinedload(UsersModel.security_questions),
                )
                .filter(UsersModel.username == username)
                .first()
            )
            return user
        except SQLAlchemyError as e:
            print(f"[DB Error] get_user_by_username failed: {e}")
            raise
        except Exception as e:
            print(f"[Unexpected Error] get_user_by_username failed: {e}")
            raise

    def update_user_token(self, session: Session,
                          username: str, token_hash: bytes | None, expires_at: str | None) -> None:
        """Update a user's remember me token hash and expiration."""
        try:
            user = session.query(UsersModel).filter_by(username=username).first()
            if user:
                user.token_hash = token_hash
                user.expires_at = expires_at
                session.add(user)   # Mark as modified
                # Session commit is handled by the calling service layer
        except SQLAlchemyError as e:
            print(f"SQLAlchemyError in update_user_token: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error in update_user_token: {e}")
            raise

    def get_user_full_name(self, session: Session, username: str) -> str:
        """Get user's full name from profile."""
        try:
            user = (session.query(UsersModel).options(joinedload(UsersModel.user_profile)).
                    filter_by(username=username).first())
            if user and user.user_profile:  # Changed to user_profile
                return user.user_profile.display_name or "کاربر میهمان"
            return "کاربر میهمان"
        except SQLAlchemyError as e:
            print(f"SQLAlchemyError in get_user_full_name: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error in get_user_full_name: {e}")
            raise

    def create_login_log_entry(self, session: Session, user_id: int, login_time: datetime) -> LoginLogsModel:
        """Creates a new record in the login_logs table and returns it."""
        new_log = LoginLogsModel(
            user_id=user_id,
            login_time=login_time.isoformat(),
            status='success' or 'auto_login_success'
        )
        session.add(new_log)
        session.flush()
        return new_log

    def update_logout_time(self, session: Session, log_id: int, logout_time: datetime) -> None:
        """Finds a log entry by its ID and updates the logout_time."""
        log_entry = session.get(LoginLogsModel, log_id)
        if log_entry:
            log_entry.logout_time = logout_time.isoformat()
            # You could also calculate and store the duration here
            login_dt = datetime.fromisoformat(log_entry.login_time)
            duration_seconds = (logout_time - login_dt).total_seconds()
            log_entry.time_on_app = int(duration_seconds)

    def record_failed_login(self, session: Session, user: UsersModel) -> None:
        """
        Increments the failed login counter for a user and locks their
        account if the threshold is exceeded.
        """
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
            lockout_time = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            user.lockout_until_utc = lockout_time
            print(f"User '{user.username}' account locked until {lockout_time.isoformat()} UTC.")

    def reset_login_attempts(self, session: Session, user: UsersModel) -> None:
        """Resets the failed login counter and unlocks the account."""
        if user.failed_login_attempts > 0 or user.lockout_until_utc is not None:
            user.failed_login_attempts = 0
            user.lockout_until_utc = None
