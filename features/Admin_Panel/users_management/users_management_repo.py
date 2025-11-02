# features/Admin_Panel/users_management/users_management_repo.py

from datetime import datetime
from sqlalchemy.orm import Session
from shared.orm_models.users_models import (
    UsersModel,
    DeletedUsersModel,
    EditedUsersLogModel,
)
from shared.orm_models.payroll_models import EmployeeModel


class UserManagementRepository:
    """
    Handles database operations for both Users.db and Payroll.db,
    reflecting the updated Users domain.
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
    # 👔 Payroll Database Queries
    # --------------------------------------------------------
    def get_employee_by_code(self, payroll_session: Session, employee_code: str) -> EmployeeModel | None:
        """Fetches an employee from Payroll DB by code."""
        return payroll_session.query(EmployeeModel).filter_by(employee_code=employee_code).first()

    def get_employee_by_national_id(self, payroll_session: Session, national_id: str) -> EmployeeModel | None:
        """Fetches an employee from Payroll DB by national ID."""
        return payroll_session.query(EmployeeModel).filter_by(national_id=national_id).first()

    # --------------------------------------------------------
    # 💾 Create / Update / Delete
    # --------------------------------------------------------
    def save_new_user(self, session: Session, user: UsersModel):
        """Saves a new user."""
        try:
            session.add(user)
            session.commit()
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
            deleted_record = DeletedUsersModel(
                original_user_id=user_to_delete.id,
                employee_id=user_to_delete.employee_id,
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

    # --------------------------------------------------------
    # 🧩 Cross-Database Transaction (Payroll + Users)
    # --------------------------------------------------------
    def save_new_employee_and_user(
        self,
        payroll_session: Session,
        users_session: Session,
        employee: EmployeeModel,
        user: UsersModel,
    ):
        """
        Saves a new employee (in payroll DB) and corresponding user (in users DB)
        in a coordinated transaction.
        """
        try:
            # Stage 1: Add to users DB
            users_session.add(user)
            users_session.flush()

            # Stage 2: Add to payroll DB
            payroll_session.add(employee)

            # Stage 3: Commit both
            users_session.commit()
            payroll_session.commit()

        except Exception:
            users_session.rollback()
            payroll_session.rollback()
            raise
