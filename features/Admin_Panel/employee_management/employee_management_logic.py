# Admin_Panel/employee_management/employee_management_logic.py

import uuid
from datetime import date
from decimal import Decimal
import bcrypt

from features.Admin_Panel.employee_management.employee_management_models import EmployeeFullData
from features.Admin_Panel.employee_management.employee_management_repo import EmployeeManagementRepository
from shared.orm_models.payroll_models import EmployeeModel, EmployeePayrollProfileModel
from shared.orm_models.users_models import UsersModel, UserProfileModel


class UserManagementLogic:
    def __init__(self, repository: EmployeeManagementRepository, users_session_factory, payroll_session_factory):
        self._repo = repository
        self.UsersSession = users_session_factory
        self.PayrollSession = payroll_session_factory

    def get_all_employees_for_display(self) -> list[EmployeeFullData]:
        """
        Fetches all employees and their corresponding user data, combining them
        into a complete DTO for the _view.
        """
        with self.PayrollSession() as p_sess, self.UsersSession() as u_sess:
            employees = self._repo.get_all_employees_with_details(p_sess)
            national_ids = [emp.national_id for emp in employees if emp.national_id]
            users_map = self._repo.get_users_map(u_sess, national_ids)

            dto_list = []
            for emp in employees:
                user = users_map.get(emp.national_id)
                if emp.payroll_profile and user and user.user_profile:
                    dto_list.append(EmployeeFullData(
                        employee_id=emp.employee_id,
                        first_name=emp.first_name,
                        last_name=emp.last_name,
                        national_id=emp.national_id,
                        date_of_birth=emp.date_of_birth,
                        hire_date=emp.hire_date,
                        email=emp.email,
                        phone_number=emp.phone_number,
                        user_id=user.id,
                        username=user.username,
                        role=user.role,
                        is_active=(user.active == 1),
                        payment_type=emp.payroll_profile.payment_type,
                        custom_daily_payment_rials=emp.payroll_profile.custom_daily_payment_rials or Decimal(0),
                        commission_rate=emp.payroll_profile.commission_rate or Decimal(0),
                        marital_status=emp.payroll_profile.marital_status,
                        children_count=emp.payroll_profile.children_count
                    ))
            return dto_list

    def save_employee(self, data: EmployeeFullData):
        """Dispatches to the correct create or update method."""
        if data.employee_id and data.user_id:
            self._update_existing_employee(data)
        else:
            self._create_new_employee_and_user(data)

    def _create_new_employee_and_user(self, data: EmployeeFullData):
        """Creates a new, fully linked Employee and User record."""
        # --- Validation ---
        if not data.first_name or not data.last_name:
            raise ValueError("نام و نام خانوادگی نمی‌تواند خالی باشد.")
        if not data.username or not data.password:
            raise ValueError("نام کاربری و رمز عبور برای کاربر جدید ضروری است.")
        if not data.national_id:
            raise ValueError("کد ملی برای ایجاد لینک بین حساب کاربری و کارمند ضروری است.")

        # --- Create Users.db objects ---
        hashed_password = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt())
        user = UsersModel(
            username=data.username,
            password_hash=hashed_password,
            role=data.role,
            active=1 if data.is_active else 0
        )
        profile = UserProfileModel(
            full_name=f"{data.first_name} {data.last_name}",
            national_id=data.national_id,
            role_fa="..."  # Placeholder for now
        )

        # --- Create Payroll.db objects ---
        employee = EmployeeModel(
            employee_id=str(uuid.uuid4()),
            first_name=data.first_name,
            last_name=data.last_name,
            national_id=data.national_id,
            date_of_birth=data.date_of_birth,
            hire_date=data.hire_date or date.today(),
            email=data.email,
            phone_number=data.phone_number,
            payroll_profile=EmployeePayrollProfileModel(
                payment_type=data.payment_type,
                custom_daily_payment_rials=data.custom_daily_payment_rials,
                commission_rate=data.commission_rate,
                marital_status=data.marital_status,
                children_count=data.children_count
            )
        )

        with self.PayrollSession() as p_sess, self.UsersSession() as u_sess:
            self._repo.save_new_employee_and_user(p_sess, u_sess, employee, user, profile)

    def _update_existing_employee(self, data: EmployeeFullData):
        """Updates an existing, linked Employee and User record."""
        # --- Prepare data dictionaries for the repository update method ---
        employee_changes = {
            'first_name': data.first_name, 'last_name': data.last_name,
            'national_id': data.national_id, 'date_of_birth': data.date_of_birth,
            'hire_date': data.hire_date, 'email': data.email, 'phone_number': data.phone_number
        }

        user_changes = {'role': data.role, 'active': 1 if data.is_active else 0}
        if data.password:  # Only update password if a new one is provided
            user_changes['password_hash'] = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt())

        profile_changes = {'full_name': f"{data.first_name} {data.last_name}"}

        payroll_changes = {
            'payment_type': data.payment_type,
            'custom_daily_payment_rials': data.custom_daily_payment_rials,
            'commission_rate': data.commission_rate,
            'marital_status': data.marital_status,
            'children_count': data.children_count
        }

        with self.PayrollSession() as p_sess, self.UsersSession() as u_sess:
            self._repo.update_employee_and_user(payroll_session=p_sess, users_session=u_sess,
                                                employee_id=data.employee_id, user_id=data.user_id,
                                                employee_changes=employee_changes, user_changes=user_changes,
                                                profile_changes=profile_changes,
                                                payroll_profile_changes=payroll_changes)

    def delete_employee(self, employee_id: str, user_national_id: str):
        """Deletes an employee from Payroll.db and their user from Users.db."""
        if not employee_id and user_national_id:
            raise ValueError("شناسه کارمند و کد ملی برای حذف ضروری است.")

        with self.PayrollSession() as p_sess, self.UsersSession() as u_sess:
            self._repo.delete_employee_and_user(payroll_session=p_sess, users_session=u_sess,
                                                employee_id=employee_id, national_id=user_national_id)
