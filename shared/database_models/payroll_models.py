# shared/database_models/payroll_models.py

from sqlalchemy import (Text, Integer, Float, Date, CheckConstraint, Index, ForeignKey, String, Numeric)
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from datetime import datetime

BasePayroll = declarative_base()


class EmployeeModel(BasePayroll):
    """
    Stores core personal and employment details for each employee.
    """
    __tablename__ = 'employees'
    employee_id: Mapped[str] = mapped_column(String(36), primary_key=True) # Using UUID as PK
    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    last_name: Mapped[str] = mapped_column(Text, nullable=False)
    national_id: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    date_of_birth: Mapped[Date | None] = mapped_column(Date, nullable=True)
    hire_date: Mapped[Date] = mapped_column(Date, nullable=False)
    email: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)
    phone_number: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)

    payroll_profile: Mapped["EmployeePayrollProfileModel"] = relationship(
        back_populates="employee", uselist=False, cascade="all, delete-orphan"
    )
    payroll_records: Mapped[list["PayrollRecordModel"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )


class SystemConstantModel(BasePayroll):
    """
    Stores system-wide government-mandated values or configuration settings for a given year.
    This is the "source of truth" for calculations.
    """
    __tablename__ = 'system_constants'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True) # e.g., 'MIN_DAILY_WAGE_RIAL_2025', 'OVERTIME_RATE_PCT', 'INSURANCE_EMP_RATE_PCT', 'TAX_EXEMPT_ANNUAL_TOMANS_2025'
    name: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[Numeric] = mapped_column(Numeric(precision=18, scale=4), nullable=False) # Use Numeric for precision
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True) # e.g., 'Rials', 'Tomans', '%'
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class EmployeePayrollProfileModel(BasePayroll):
    """Stores the specific payroll setup for each employee."""
    __tablename__ = 'employee_payroll_profiles'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[str] = mapped_column(
        ForeignKey('employees.employee_id'), nullable=False, unique=True, index=True
    )

    payment_type: Mapped[str] = mapped_column(String(50), default='Full-time')

    # Use Numeric for monetary values and clearer naming
    custom_daily_payment_rials: Mapped[Numeric | None] = mapped_column(Numeric(precision=18, scale=2), nullable=True, default=None)
    commission_rate: Mapped[Numeric] = mapped_column(Numeric(precision=5, scale=4), default=0.0)

    marital_status: Mapped[str] = mapped_column(String(20), default='Single')
    children_count: Mapped[int] = mapped_column(Integer, default=0)

    employee: Mapped["EmployeeModel"] = relationship(back_populates="payroll_profile")
    custom_components: Mapped[list["EmployeeCustomPayrollComponentModel"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("payment_type IN ('Full-time', 'Part-time', 'Commission')"),
        CheckConstraint("marital_status IN ('Single', 'Married')"),
    )


class EmployeeCustomPayrollComponentModel(BasePayroll):
    """A flexible table for custom, employee-specific allowances or deductions."""
    __tablename__ = 'employee_custom_payroll_components'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey('employee_payroll_profiles.id'), index=True)

    name: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[Numeric] = mapped_column(Numeric(precision=18, scale=2), nullable=False)
    type: Mapped[str] = mapped_column(String(20), default='Allowance') # 'Allowance' or 'Deduction'

    profile: Mapped["EmployeePayrollProfileModel"] = relationship(back_populates="custom_components")

    __table_args__ = (
        CheckConstraint("type IN ('Allowance', 'Deduction')"),
    )
    __mapper_args__ = {
        "eager_defaults": True,
    }


class SalaryComponentModel(BasePayroll):
    """
    Defines types of earnings and deductions that can be part of a salary slip.
    These are standard components, not employee-specific custom ones.
    """
    __tablename__ = 'salary_components'
    component_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True) # e.g., 'Basic Salary', 'Overtime Pay', 'Employee Insurance', 'Income Tax'
    type: Mapped[str] = mapped_column(String(20), default='Earning') # 'Earning' or 'Deduction'
    is_taxable_for_income_tax: Mapped[bool] = mapped_column(nullable=False, default=True)
    is_deductible_for_taxable_income: Mapped[bool] = mapped_column(nullable=False, default=False)
    is_base_for_insurance_calculation: Mapped[bool] = mapped_column(nullable=False, default=True)
    default_rate_percentage: Mapped[Numeric | None] = mapped_column(Numeric(precision=5, scale=4), nullable=True) # e.g., 0.07 for 7% insurance

    payroll_details: Mapped[list["PayrollComponentDetailModel"]] = relationship(
        back_populates="salary_component", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("type IN ('Earning', 'Deduction')"),
    )


class PayrollRecordModel(BasePayroll):
    """
    Stores the summarized payroll results for each employee for a specific pay period.
    This is the main record for a salary slip.
    """
    __tablename__ = 'payroll_records'
    payroll_id: Mapped[str] = mapped_column(String(36), primary_key=True) # Using UUID as PK
    employee_id: Mapped[str] = mapped_column(
        ForeignKey('employees.employee_id'), nullable=False, index=True
    )
    pay_period_start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    pay_period_end_date: Mapped[Date] = mapped_column(Date, nullable=False)
    base_working_days_in_period: Mapped[int] = mapped_column(Integer, nullable=False)
    overtime_hours_in_period: Mapped[Numeric] = mapped_column(Numeric(precision=10, scale=2), default=0.0)

    gross_income_tomans: Mapped[Numeric] = mapped_column(Numeric(precision=18, scale=2), nullable=False)
    total_deductions_tomans: Mapped[Numeric] = mapped_column(Numeric(precision=18, scale=2), nullable=False)
    taxable_income_tomans: Mapped[Numeric] = mapped_column(Numeric(precision=18, scale=2), nullable=False)
    calculated_tax_tomans: Mapped[Numeric] = mapped_column(Numeric(precision=18, scale=2), nullable=False)
    calculated_insurance_tomans: Mapped[Numeric] = mapped_column(Numeric(precision=18, scale=2), nullable=False)
    net_income_tomans: Mapped[Numeric] = mapped_column(Numeric(precision=18, scale=2), nullable=False)

    status: Mapped[str] = mapped_column(String(20), default='Draft') # e.g., 'Draft', 'Finalized', 'Paid'
    calculation_date: Mapped[datetime] = mapped_column(default=datetime.now)

    employee: Mapped["EmployeeModel"] = relationship(back_populates="payroll_records")
    component_details: Mapped[list["PayrollComponentDetailModel"]] = relationship(
        back_populates="payroll_record", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("status IN ('Draft', 'Finalized', 'Paid')"),
    )


class PayrollComponentDetailModel(BasePayroll):
    """
    Stores the specific calculated amount for each salary component
    within a given payroll record, providing the detailed breakdown for a salary slip.
    """
    __tablename__ = 'payroll_component_details'
    detail_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payroll_id: Mapped[str] = mapped_column(
        ForeignKey('payroll_records.payroll_id'), nullable=False, index=True
    )
    component_id: Mapped[int] = mapped_column(
        ForeignKey('salary_components.component_id'), nullable=False, index=True
    )
    amount_tomans: Mapped[Numeric] = mapped_column(Numeric(precision=18, scale=2), nullable=False)
    calculation_details: Mapped[str | None] = mapped_column(Text, nullable=True) # e.g., "20 hours @ 61250 Tomans/hr"

    payroll_record: Mapped["PayrollRecordModel"] = relationship(back_populates="component_details")
    salary_component: Mapped["SalaryComponentModel"] = relationship(back_populates="payroll_details")


class TaxBracketModel(BasePayroll):
    """
    Stores progressive tax brackets for each year.
    Each row represents a range and its tax rate.
    """
    __tablename__ = 'tax_brackets'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    lower_bound: Mapped[Numeric] = mapped_column(Numeric(precision=18, scale=2), nullable=False)
    upper_bound: Mapped[Numeric | None] = mapped_column(Numeric(precision=18, scale=2), nullable=True)
    rate: Mapped[Numeric] = mapped_column(Numeric(precision=5, scale=4), nullable=False) # e.g., 0.10 for 10%
