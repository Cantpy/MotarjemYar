# Admin_Panel/employee_management/employee_management_repo.py
from typing import List, Type

from sqlalchemy.orm import Session, joinedload
from shared.database_models.user_models import UsersModel, UserProfileModel
from shared.database_models.payroll_models import EmployeeModel, EmployeePayrollProfileModel


class EmployeeManagementRepository:
    """
    Repository for managing Employee records, which spans both
    the Payroll.db (EmployeeModel) and Users.db (UsersModel).
    """

    def get_all_employees_with_details(self, payroll_session: Session) -> list[EmployeeModel]:
        """Fetches all employees with their payroll profile pre-loaded."""
        return payroll_session.query(EmployeeModel).options(
            joinedload(EmployeeModel.payroll_profile)
        ).order_by(EmployeeModel.last_name).all()

    def get_users_map(self, users_session: Session, national_ids: list[str]) -> dict:
        """
        Fetches UsersModel objects for a list of national IDs and returns a
        map of {national_id: UsersModel}.
        """
        if not national_ids:
            return {}
        users = users_session.query(UsersModel).options(
            joinedload(UsersModel.user_profile)
        ).filter(
            UsersModel.user_profile.has(UserProfileModel.national_id.in_(national_ids))
        ).all()
        return {u.user_profile.national_id: u for u in users if u.user_profile}

    def save_new_employee_and_user(self, payroll_session: Session, users_session: Session, employee: EmployeeModel,
                                   user: UsersModel, profile: UserProfileModel):
        """Saves a new employee and user across two databases in a coordinated transaction."""
        try:
            users_session.add(user)
            users_session.flush()
            profile.user_id = user.id
            users_session.add(profile)

            payroll_session.add(employee)

            users_session.commit()
            payroll_session.commit()
        except Exception:
            users_session.rollback()
            payroll_session.rollback()
            raise

    # --- FIX: This method now correctly accepts both sessions and all necessary data dictionaries ---
    def update_employee_and_user(self, payroll_session: Session, users_session: Session,
                                 employee_id: str, user_id: int,
                                 employee_changes: dict, user_changes: dict,
                                 profile_changes: dict, payroll_profile_changes: dict):
        """Updates records for a single employee across both databases."""
        try:
            # Update Payroll.db
            payroll_session.query(EmployeeModel).filter_by(employee_id=employee_id).update(employee_changes)
            payroll_session.query(EmployeePayrollProfileModel).filter_by(employee_id=employee_id).update(
                payroll_profile_changes)

            # Update Users.db
            users_session.query(UsersModel).filter_by(id=user_id).update(user_changes)
            users_session.query(UserProfileModel).filter_by(user_id=user_id).update(profile_changes)

            payroll_session.commit()
            users_session.commit()
        except Exception:
            payroll_session.rollback()
            users_session.rollback()
            raise

    # --- FIX: This method now correctly accepts both sessions and the linking national_id ---
    def delete_employee_and_user(self, payroll_session: Session, users_session: Session,
                                 employee_id: str, national_id: str):
        """Deletes an employee from Payroll.db and their linked user from Users.db."""
        try:
            # Delete from Payroll.db (cascade will handle the payroll profile)
            payroll_session.query(EmployeeModel).filter_by(employee_id=employee_id).delete()

            # Find the user by the shared national_id and delete them
            # The cascade on the UsersModel will handle the user_profile
            user_to_delete = users_session.query(UsersModel).join(UserProfileModel).filter(
                UserProfileModel.national_id == national_id
            ).first()
            if user_to_delete:
                users_session.delete(user_to_delete)

            payroll_session.commit()
            users_session.commit()
        except Exception:
            payroll_session.rollback()
            users_session.rollback()
            raise
