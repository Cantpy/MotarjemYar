# shared/dtos/payroll_dto.py

from dataclasses import dataclass


@dataclass
class EmployeeDTO:
    """A simplified Data Transfer Object for Employee details."""
    employee_id: str
    first_name: str
    last_name: str
    national_id: str
    date_of_birth: str | None
    hire_date: str
    email: str | None
    phone_number: str | None
    created_at: str
    updated_at: str | None


@dataclass
class SystemConstantDTO:
    """A simplified Data Transfer Object for System Constant details."""
    id: int
    year: int
    code: str
    name: str
    value: float
    unit: str | None
    description: str | None


@dataclass
class EmployeePayrollProfileDTO:
    """A simplified Data Transfer Object for Employee Payroll Profile details."""
    id: int
    employee_id: str
    payment_type: str
    custom_daily_payment_rials: float | None
    commission_rate: float
    marital_status: str
    children_count: int


@dataclass
class EmployeeCustomPayrollComponentDTO:
    """A simplified Data Transfer Object for Employee Custom Payroll Component details."""
    id: int
    profile_id: int
    name: str
    value: float
    type: str


@dataclass
class SalaryComponentDTO:
    """A simplified Data Transfer Object for Salary Component details."""
    component_id: int
    name: str
    type: str
    is_taxable_for_income_tax: bool
    is_deductible_for_taxable_income: bool
    is_base_for_insurance_calculation: bool
    default_rate_percentage: float | None


@dataclass
class PayrollRecordDTO:
    """A simplified Data Transfer Object for Payroll Record details."""
    payroll_id: str
    employee_id: str
    pay_period_start_date: str
    pay_period_end_date: str
    base_working_days_in_period: int
    overtime_hours_in_period: float
    gross_income_tomans: float
    total_deductions_tomans: float
    taxable_income_tomans: float
    calculated_tax_tomans: float
    calculated_insurance_tomans: float
    net_income_tomans: float
    status: str
    calculation_date: str


@dataclass
class PayrollComponentDetailDTO:
    """A simplified Data Transfer Object for Payroll Component Detail."""
    detail_id: int
    payroll_id: str
    component_id: int
    amount_tomans: float
    calculation_details: str | None


@dataclass
class TaxBracketDTO:
    """A simplified Data Transfer Object for Tax Bracket details."""
    id: int
    year: int
    lower_bound: float
    upper_bound: float | None
    rate: float
