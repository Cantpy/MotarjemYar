# Admin_Panel/employee_management/employee_management_models.py

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class EmployeeFullData:
    """A DTO for transferring Employee data. Does NOT contain user/login info."""
    employee_id: str | None = None  # This now acts as the link to the UsersModel
    employee_code: str = ""

    # Personal Info (from EmployeeModel)
    first_name: str = ""
    last_name: str = ""
    national_id: str = ""
    date_of_birth: date | None = None
    hire_date: date | None = None
    email: str = ""
    phone_number: str = ""

    # Payroll Info (from EmployeePayrollProfileModel)
    employment_type: str = "full_time"
    base_salary_rials: Decimal = Decimal(0)
    hourly_rate_rials: Decimal = Decimal(0)
    commission_rate_pct: Decimal = Decimal(0)
    marital_status: str = "Single"
    children_count: int = 0
