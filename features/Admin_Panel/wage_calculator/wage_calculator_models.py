# features/Admin_Panel/wage_calculator/wage_calculator_models.py

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, List
from shared.orm_models.payroll_models import EmploymentType


@dataclass
class PayrollRunEmployee:
    """A DTO for one row in the main employee list for a given pay run."""
    payroll_id: str | None
    employee_id: str
    full_name: str
    gross_income: Decimal
    net_income: Decimal
    status: str


@dataclass
class PayrollComponent:
    """Represents one line item (earning or deduction) on a payslip."""
    name: str
    display_name: str
    type: str  # 'Earning' or 'Deduction'
    amount: Decimal


@dataclass
class CommissionDetail:
    """Represents the details of a single commissionable invoice for a payslip."""
    invoice_number: str
    customer_name: str
    total_price: Decimal
    translator_share: Decimal


@dataclass
class TranslationOffice:
    """"""
    name: str
    registration: str
    representative: str
    manager: str
    address: str
    phone: str


@dataclass
class PayslipData:
    """The complete data needed to display a finalized payslip in the preview."""
    payroll_id: str
    employee_code: str
    employee_name: str
    employee_national_id: str
    pay_period_str: str
    gross_income: Decimal
    total_deductions: Decimal
    net_income: Decimal
    translation_office: TranslationOffice
    issuer: str
    components: list[PayrollComponent] = field(default_factory=list)
    _raw_data_for_save: Optional[dict] = field(default=None, repr=False)

    employment_type: EmploymentType = EmploymentType.FULL_TIME
    hours_worked: Optional[Decimal] = None
    commissions: Optional[List[CommissionDetail]] = field(default_factory=list)


@dataclass
class EmployeeInfo:
    """A simple DTO for employee selection lists."""
    employee_id: str
    full_name: str
