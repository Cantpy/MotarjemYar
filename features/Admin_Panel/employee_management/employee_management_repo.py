# features/Admin_Panel/employee_management/employee_management_repo.py

from sqlalchemy.orm import Session, joinedload
from shared.orm_models.payroll_models import (EmployeeModel, EmployeePayrollProfileModel, EmployeeRoleModel,
                                              DeletedEmployeeModel, EditedEmployeeLogModel)


class EmployeeManagementRepository:
    """
    Repository for managing Employee records, which spans both
    the Payroll.db (EmployeeModel) and Users.db (UsersModel).
    """

    def get_all_employees_with_details(self, payroll_session: Session) -> list[EmployeeModel]:
        """Fetches all employees with their payroll profile and role pre-loaded."""
        return payroll_session.query(EmployeeModel).options(
            joinedload(EmployeeModel.payroll_profile),
            joinedload(EmployeeModel.role)
        ).order_by(EmployeeModel.last_name).all()

    def get_all_roles(self, payroll_session: Session) -> list[EmployeeRoleModel]:
        """Fetches all active employee roles."""
        return payroll_session.query(EmployeeRoleModel).filter_by(active=True).order_by(EmployeeRoleModel.role_name_fa).all()

    def get_edit_logs_for_employee(self, payroll_session: Session, employee_id: str) -> list[EditedEmployeeLogModel]:
        """Fetches all change logs for a given employee, ordered by most recent."""
        return payroll_session.query(EditedEmployeeLogModel)\
            .filter_by(employee_id=employee_id)\
            .order_by(EditedEmployeeLogModel.edited_at.desc())\
            .all()

    def save_new_employee(self, payroll_session: Session, employee: EmployeeModel):
        """Saves a new employee and their payroll profile to the database."""
        try:
            payroll_session.add(employee)
            payroll_session.commit()
        except Exception:
            payroll_session.rollback()
            raise

    def update_employee(self, payroll_session: Session, employee_id: str,
                        employee_changes: dict, payroll_profile_changes: dict,
                        edit_logs: list[EditedEmployeeLogModel]):
        """Updates records for a single employee in the payroll database."""
        try:
            if edit_logs:
                payroll_session.add_all(edit_logs)

            payroll_session.query(EmployeeModel).filter_by(employee_id=employee_id).update(employee_changes)
            payroll_session.query(EmployeePayrollProfileModel).filter_by(employee_id=employee_id).update(
                payroll_profile_changes)

            payroll_session.commit()
        except Exception:
            payroll_session.rollback()
            raise

    def archive_employee(self, payroll_session: Session,
                         employee_to_delete: EmployeeModel,
                         deleted_by: str):
        """Moves an employee to the deleted table."""
        try:
            # Note: The '...' is a placeholder for the actual data mapping
            deleted_record = DeletedEmployeeModel(
                original_employee_id=employee_to_delete.employee_id,
                employee_code=employee_to_delete.employee_code,
                first_name=employee_to_delete.first_name,
                last_name=employee_to_delete.last_name,
                national_id=employee_to_delete.national_id,
                insurance_number=employee_to_delete.insurance_number,
                hire_date=employee_to_delete.hire_date,
                termination_date=employee_to_delete.termination_date,
                deleted_by=deleted_by
            )
            payroll_session.add(deleted_record)
            payroll_session.delete(employee_to_delete)
            payroll_session.commit()
        except Exception:
            payroll_session.rollback()
            raise

    def get_employee_by_id(self, payroll_session: Session, employee_id: str) -> EmployeeModel | None:
        return payroll_session.query(EmployeeModel).options(
            joinedload(EmployeeModel.payroll_profile),
            joinedload(EmployeeModel.role)
        ).filter(EmployeeModel.employee_id == employee_id).first()

    def get_employee_by_national_id(self, payroll_session: Session, national_id: str) -> EmployeeModel | None:
        return payroll_session.query(EmployeeModel).options(joinedload(EmployeeModel.payroll_profile)).filter(
            EmployeeModel.national_id == national_id).first()

    def get_employee_by_code(self, payroll_session: Session, employee_code: str) -> EmployeeModel | None:
        return payroll_session.query(EmployeeModel).options(joinedload(EmployeeModel.payroll_profile)).filter(
            EmployeeModel.employee_code == employee_code).first()
