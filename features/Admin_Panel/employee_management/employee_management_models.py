# Admin_Panel/employee_management/employee_management_models.py

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass
class EmployeeFullData:
    """A DTO for transferring all Employee data between UI and logic."""
    employee_id: str | None = None
    # Personal Info (from EmployeeModel)
    first_name: str = ""
    last_name: str = ""
    national_id: str = ""
    date_of_birth: date | None = None
    hire_date: date | None = None
    email: str = ""
    phone_number: str = ""
    # Payroll Info (from EmployeePayrollProfileModel)
    payment_type: str = "Full-time"
    custom_daily_payment_rials: Decimal = Decimal(0)
    commission_rate: Decimal = Decimal(0)
    marital_status: str = "Single"
    children_count: int = 0

    # Users.db -> UsersModel
    user_id: int | None = None
    username: str = ""
    password: str = ""  # For creation/update
    role: str = "clerk"
    is_active: bool = True
