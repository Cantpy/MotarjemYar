# Admin_Panel/wage_calculator/wage_calculator_models.py

from dataclasses import dataclass


@dataclass
class EmployeeData:
    """A DTO to hold all relevant data for one employee to display in the table."""
    user_id: int
    username: str
    full_name: str
    role: str
    payment_type: str
    payment_detail: str


@dataclass
class PayrollStats:
    """Holds the data for the top-level KPI cards."""
    total_employees: int
    total_payroll_month: int
    average_salary_month: int


@dataclass
class CalculatedWage:
    """Holds the detailed results of a single wage calculation."""
    employee_name: str
    total_wage: float
    details: str    # A multi-line string explaining the calculation```


@dataclass
class RoleSummaryData:
    """Holds the calculated statistics for a single role."""
    role_key: str       # e.g., 'admin', 'clerk'
    role_name: str      # e.g., 'مدیر', 'کارمند'
    count: int = 0
    total_salary: int = 0
    average_salary: int = 0
