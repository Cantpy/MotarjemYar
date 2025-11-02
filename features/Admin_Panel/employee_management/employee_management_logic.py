# Admin_Panel/employee_management/employee_management_logic.py

from datetime import date
from decimal import Decimal
from features.Admin_Panel.employee_management.employee_management_models import EmployeeFullData
from features.Admin_Panel.employee_management.employee_management_repo import EmployeeManagementRepository
from features.Admin_Panel.employee_management import employee_management_validator as validator
from shared.orm_models.payroll_models import (EmployeeModel, EmployeePayrollProfileModel, EmploymentType)
from shared.session_provider import ManagedSessionProvider, SessionManager


class UserManagementLogic:
    """
    Business logic layer for managing Employee records, including validation, creation, update, and safe deletion.
    """
    def __init__(self, repository: EmployeeManagementRepository,
                 payroll_engine: ManagedSessionProvider):
        self._repo = repository
        self._payroll_session = payroll_engine

    def _sanitize_persian_numerals(self, text: str) -> str:
        """Converts Persian numerals in a string to English equivalents."""
        if not text:
            return ""
        persian_to_english = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
        return text.translate(persian_to_english)

    def _validate_employee_data(self, data: EmployeeFullData, is_edit: bool = False):
        """Runs all validations for employee data."""
        errors = []

        # MODIFIED: Sanitize national ID before validation
        national_id_to_validate = self._sanitize_persian_numerals(data.national_id)

        validation_checks = {
            "نام": validator.validate_required_field(data.first_name, "نام"),
            "نام خانوادگی": validator.validate_required_field(data.last_name, "نام خانوادگی"),
            "کد پرسنلی": validator.validate_required_field(data.employee_code, "کد پرسنلی"),
            "کد ملی": validator.validate_national_id(national_id_to_validate),
            "شماره تلفن": validator.validate_phone_number(data.phone_number),
            "ایمیل": validator.validate_email(data.email),
            "تاریخ استخدام": validator.validate_hire_date(data.hire_date),
            "تاریخ تولد": validator.validate_birth_date(data.date_of_birth),
        }

        for field, (is_valid, error_message) in validation_checks.items():
            if not is_valid:
                errors.append(error_message)

        if errors:
            # The message is formatted for clear display in the dialog
            error_summary = "لطفاً خطاهای زیر را اصلاح کنید:\n\n" + "\n".join(f"• {e}" for e in errors)
            raise ValueError(error_summary)

    def get_all_employees_for_display(self) -> list[EmployeeFullData]:
        """ Fetches all employees and converts them to DTOs for the view. """
        with self._payroll_session() as p_sess:
            employees = self._repo.get_all_employees_with_details(p_sess)
            dto_list = []
            for emp in employees:
                if emp.payroll_profile:
                    dto_list.append(EmployeeFullData(
                        employee_id=emp.employee_id,
                        employee_code=emp.employee_code,
                        first_name=emp.first_name,
                        last_name=emp.last_name,
                        national_id=emp.national_id,
                        date_of_birth=emp.date_of_birth,
                        hire_date=emp.hire_date,
                        email=emp.email,
                        phone_number=emp.phone_number,
                        employment_type=emp.payroll_profile.employment_type.name,
                        base_salary_rials=emp.payroll_profile.base_salary_rials or Decimal(0),
                        hourly_rate_rials=emp.payroll_profile.hourly_rate_rials or Decimal(0),
                        commission_rate_pct=emp.payroll_profile.commission_rate_pct or Decimal(0),
                        marital_status=emp.payroll_profile.marital_status,
                        children_count=emp.payroll_profile.children_count
                    ))
            return dto_list

    def save_employee(self, data: EmployeeFullData):
        """Dispatches to the correct create or update method for an employee profile."""
        data.national_id = self._sanitize_persian_numerals(data.national_id)
        data.phone_number = self._sanitize_persian_numerals(data.phone_number)

        # The logic is now based on whether employee_code exists, which signifies an existing record
        with self._payroll_session() as p_sess:
            existing_employee = self._repo.get_employee_by_id(p_sess, data.employee_id)

        if existing_employee:
            self._update_existing_employee(data)
        else:
            self._create_new_employee(data)

    def _create_new_employee(self, data: EmployeeFullData):
        """Creates a new Employee record. Assumes the User already exists."""
        self._validate_employee_data(data, is_edit=False)

        employee = EmployeeModel(
            employee_code=data.employee_code,
            first_name=data.first_name,
            last_name=data.last_name,
            national_id=data.national_id,
            date_of_birth=data.date_of_birth,
            hire_date=data.hire_date or date.today(),
            email=data.email or None,
            phone_number=data.phone_number or None,
            payroll_profile=EmployeePayrollProfileModel(
                employment_type=EmploymentType[data.employment_type].value,
                base_salary_rials=data.base_salary_rials,
                hourly_rate_rials=data.hourly_rate_rials,
                commission_rate_pct=data.commission_rate_pct,
                marital_status=data.marital_status,
                children_count=data.children_count
            )
        )

        with self._payroll_session() as p_sess:
            if self._repo.get_employee_by_code(p_sess, data.employee_code):
                raise ValueError(f"کد پرسنلی '{data.employee_code}' قبلا استفاده شده است.")
            if self._repo.get_employee_by_national_id(p_sess, data.national_id):
                raise ValueError(f"کد ملی '{data.national_id}' قبلا ثبت شده است.")

            self._repo.save_new_employee(p_sess, employee)

    def _update_existing_employee(self, data: EmployeeFullData):
        """Updates an existing Employee record."""
        self._validate_employee_data(data, is_edit=True)
        with self._payroll_session() as p_sess:
            # Fetch current state to compare for logging
            current_employee_orm = self._repo.get_employee_by_id(p_sess, data.employee_id)
            if not current_employee_orm:
                raise ValueError("Employee not found for update.")

            # (Optional) Implement detailed field change logging here...
            edit_logs = []

            employee_changes = {
                'first_name': data.first_name, 'last_name': data.last_name,
                'national_id': data.national_id, 'date_of_birth': data.date_of_birth,
                'hire_date': data.hire_date, 'email': data.email, 'phone_number': data.phone_number,
            }

            payroll_changes = {
                'employment_type': EmploymentType[data.employment_type],
                'base_salary_rials': data.base_salary_rials,
                'hourly_rate_rials': data.hourly_rate_rials,
                'commission_rate_pct': data.commission_rate_pct,
                'marital_status': data.marital_status,
                'children_count': data.children_count
            }

            self._repo.update_employee(payroll_session=p_sess,
                                       employee_id=data.employee_id,
                                       employee_changes=employee_changes,
                                       payroll_profile_changes=payroll_changes,
                                       edit_logs=edit_logs)

    def delete_employee(self, employee_id: str):
        """Archives an employee. The user account is deactivated separately."""
        if not employee_id:
            raise ValueError("شناسه کارمند برای حذف ضروری است.")

        with self._payroll_session() as p_sess:
            employee_to_delete = self._repo.get_employee_by_id(p_sess, employee_id)
            if not employee_to_delete:
                raise ValueError("کارمند مورد نظر برای حذف یافت نشد.")

            user_info = SessionManager().get_session()
            username = user_info.full_name or user_info.username or "ناشناس"

            self._repo.archive_employee(p_sess, employee_to_delete, username)
