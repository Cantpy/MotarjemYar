# Admin_Panel/wage_calculator/wage_calculator_models.py

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class PayrollRunEmployee:
    """A DTO for one row in the main employee list for a given pay run."""
    payroll_id: str
    employee_id: str
    full_name: str
    gross_income: Decimal
    net_income: Decimal
    status: str


@dataclass
class PayrollComponent:
    """Represents one line item (earning or deduction) on a payslip."""
    name: str
    type: str  # 'Earning' or 'D'Eduction'
    amount: Decimal


@dataclass
class PayslipData:
    """The complete data needed to display a finalized payslip in the preview."""
    payroll_id: str
    employee_name: str
    employee_national_id: str  # Added for completeness
    pay_period_str: str
    gross_income: Decimal
    total_deductions: Decimal
    net_income: Decimal
    components: list[PayrollComponent] = field(default_factory=list)


@dataclass
class EmployeeInfo:
    """A simple DTO for employee selection lists."""
    employee_id: str
    full_name: str
    payment_type: str
