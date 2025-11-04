# features/Admin_Panel/users_management/users_management_repo.py

from datetime import datetime
from sqlalchemy.orm import Session
from shared.orm_models.users_models import UsersModel, DeletedUsersModel, EditedUsersLogModel


class UserManagementRepository:
    """
    Handles database operations exclusively for the Users.db.
    """

    # --------------------------------------------------------
    # 🔍 User Queries
    # --------------------------------------------------------
    def get_all_users(self, session: Session) -> list[UsersModel]:
        """Fetches all active users ordered by username."""
        return (
            session.query(UsersModel)
            .order_by(UsersModel.username)
            .all()
        )

    def get_user_by_id(self, session: Session, user_id: int) -> UsersModel | None:
        """Fetches a user by their primary key."""
        return session.query(UsersModel).filter(UsersModel.id == user_id).first()

    def get_user_by_username(self, session: Session, username: str) -> UsersModel | None:
        """Fetches a user by their username."""
        return session.query(UsersModel).filter(UsersModel.username == username).first()

    # --------------------------------------------------------
    # 💾 Create / Update / Delete
    # --------------------------------------------------------
    def save_new_user(self, session: Session, user: UsersModel):
        """Saves a new user."""
        try:
            session.add(user)
            session.commit()
            session.refresh(user) # To get the ID of the new user
        except Exception:
            session.rollback()
            raise

    def update_user(self, session: Session, user_id: int, user_changes: dict, edit_logs: list[EditedUsersLogModel]):
        """
        Updates a user's information and logs the field-level changes.
        """
        try:
            if edit_logs:
                session.add_all(edit_logs)

            session.query(UsersModel).filter_by(id=user_id).update(user_changes)
            session.commit()
        except Exception:
            session.rollback()
            raise

    def archive_user(self, session: Session, user_to_delete: UsersModel, deleted_by_username: str):
        """
        Moves a user to the deleted_users archive table
        and removes them from the active users table.
        """
        try:
            # === MODIFIED: No longer contains employee_id ===
            deleted_record = DeletedUsersModel(
                original_user_id=user_to_delete.id,
                username=user_to_delete.username,
                display_name=user_to_delete.display_name,
                role=user_to_delete.role,
                deleted_by=deleted_by_username,
                deleted_at=datetime.utcnow(),
            )

            session.add(deleted_record)
            session.delete(user_to_delete)
            session.commit()
        except Exception:
            session.rollback()
            raise
