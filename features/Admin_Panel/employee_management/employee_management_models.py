# features/Admin_Panel/employee_management/employee_management_models.py

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import List, Dict


@dataclass
class EmployeeEditLogData:
    """DTO for a single employee edit log entry."""
    edited_at: date
    edited_by: str
    field_name: str
    old_value: str
    new_value: str


@dataclass
class EmployeeFullData:
    """A DTO for transferring ALL Employee data required by the UI."""
    employee_id: str | None = None
    employee_code: str = ""

    # Personal Info (from EmployeeModel)
    first_name: str = ""
    last_name: str = ""
    national_id: str = ""
    insurance_number: str | None = None
    date_of_birth: date | None = None
    hire_date: date | None = None
    email: str = ""
    phone_number: str = ""

    # Role Info
    role_id: int | None = None
    role_name_fa: str = "تعیین نشده" # Default friendly name

    # Payroll Info (from EmployeePayrollProfileModel)
    employment_type: str = "full_time"
    base_salary_rials: Decimal = Decimal(0)
    hourly_rate_rials: Decimal = Decimal(0)
    commission_rate_pct: Decimal = Decimal(0)
    marital_status: str = "Single"
    children_count: int = 0

    # For the details view
    edit_logs: List[EmployeeEditLogData] = field(default_factory=list)
