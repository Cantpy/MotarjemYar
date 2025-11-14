# features/Admin_Panel/user_info/users_info_repo.py

from sqlalchemy.orm import Session
from shared.orm_models.users_models import UsersModel


class UserInfoRepository:
    """
    Repository for accessing and modifying user data in the database.
    """

    def get_user_by_id(self, session: Session, user_id: int) -> UsersModel | None:
        """ Fetches a user by their primary key. """
        return session.query(UsersModel).filter_by(id=user_id).first()

    def update_user(self, session: Session, user_id: int, data_to_update: dict) -> bool:
        """
        Updates a user's record with the provided data.
        Returns True on success, False on failure.
        """
        user = session.query(UsersModel).filter_by(id=user_id).first()
        if not user:
            return False

        for key, value in data_to_update.items():
            if hasattr(user, key):
                setattr(user, key, value)

        return True
