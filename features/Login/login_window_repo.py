# Login/login_window_repo.py

from sqlalchemy.orm import joinedload
from shared.orm_models.users_models import BaseUsers, UsersModel, UserProfileModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError


class LoginRepository:
    """
    Repository for user authentication and management.
    """
    def get_user_by_username(self, session: Session, username: str) -> UsersModel | None:
        """Fetch a user by username, eagerly loading their profile."""
        try:
            user = session.query(UsersModel).options(joinedload(UsersModel.user_profile)).filter_by(username=username).first()
            return user
        except SQLAlchemyError as e:
            print(f"SQLAlchemyError in get_user_by_username: {e}")
            raise   # Re-raise to allow service/_logic to handle transaction rollback
        except Exception as e:
            print(f"Unexpected error in get_user_by_username: {e}")
            raise

    def update_user_token(self, session: Session, username: str, token_hash: bytes | None, expires_at: str | None) -> None:
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
            user = session.query(UsersModel).options(joinedload(UsersModel.user_profile)).filter_by(username=username).first()
            if user and user.user_profile:  # Changed to user_profile
                return user.user_profile.full_name or "کاربر میهمان"
            return "کاربر میهمان"
        except SQLAlchemyError as e:
            print(f"SQLAlchemyError in get_user_full_name: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error in get_user_full_name: {e}")
            raise
