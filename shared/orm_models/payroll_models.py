# shared/orm_models/payroll_models.py

"""
Payroll SQLAlchemy models adapted for Full-time, Part-time and Commission employees.
Includes:
- EmploymentType Enum
- Employee, DeletedEmployee, EditedEmployeeLog
- System constants and tax brackets
- Payroll profiles, components and payroll records
- Tiny SalaryCalculator skeleton (integration point) — implement business rules in a separate service module

Notes:
- Numeric columns use high precision for monetary values (store canonical value in Rials,
    present in UI as Tomans if desired)
- Use UUID strings for employee_id and payroll_id
- Keep configuration (SSO rates, ceilings, tax brackets) in SystemConstantModel + TaxBracketModel

"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (Text, Integer, Date, DateTime, CheckConstraint, ForeignKey, String, Numeric, Boolean,
                        Enum as SQLAEnum)
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship

BasePayroll = declarative_base()


class EmploymentType(enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    COMMISSION = "commission"


def _now() -> datetime:
    return datetime.utcnow()


class EmployeeModel(BasePayroll):
    __tablename__ = "employees"

    employee_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    first_name: Mapped[str] = mapped_column(String(200), nullable=False)
    last_name: Mapped[str] = mapped_column(String(200), nullable=False)
    national_id: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)

    role_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employee_roles.role_id"),
        nullable=True,
        index=True
    )

    insurance_number: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True, index=True)
    date_of_birth: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    hire_date: Mapped[Date] = mapped_column(Date, nullable=False)
    termination_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(320), unique=True, nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now, nullable=False)

    role: Mapped[Optional["EmployeeRoleModel"]] = relationship(back_populates="employees")

    payroll_profile: Mapped[Optional["EmployeePayrollProfileModel"]] = relationship(
        back_populates="employee", uselist=False, cascade="all, delete-orphan"
    )

    payroll_records: Mapped[List["PayrollRecordModel"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Employee {self.employee_code} {self.full_name}>"


class EditedEmployeeLogModel(BasePayroll):
    """Logs changes made to an employee's record."""

    __tablename__ = "edited_employee_logs"

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # FK to employees.employee_id so historic edits remain valid even if employee_code changes
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.employee_id"), index=True, nullable=False)

    edited_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    edited_by: Mapped[str] = mapped_column(String(100), nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class DeletedEmployeeModel(BasePayroll):
    """Stores a record of employees who have been deleted from the active list (soft-archive)."""

    __tablename__ = "deleted_employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    original_employee_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    employee_code: Mapped[Optional[str]] = mapped_column(String(20), index=True)

    first_name: Mapped[str] = mapped_column(String(200), nullable=False)
    last_name: Mapped[str] = mapped_column(String(200), nullable=False)
    national_id: Mapped[Optional[str]] = mapped_column(String(10), index=True)
    insurance_number: Mapped[Optional[str]] = mapped_column(String(50), index=True)

    hire_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    termination_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)

    deleted_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    deleted_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class SystemConstantModel(BasePayroll):
    """Stores system-wide government-mandated values or configuration settings for a given year.

    Examples of `code`:
      - 'MIN_MONTHLY_WAGE_RIAL_1404'
      - 'SSO_EMPLOYEE_PCT'
      - 'SSO_EMPLOYER_PCT'
      - 'SSO_BASE_CEILING_RIAL_1404'
    """

    __tablename__ = "system_constants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(precision=24, scale=4), nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class EmployeePayrollProfileModel(BasePayroll):
    """Stores the specific payroll setup for each employee.

    This keeps employment-type-specific rates (monthly, hourly, commission) and flags such as
    `insured` which determine whether SSO applies.
    """

    __tablename__ = "employee_payroll_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.employee_id"), nullable=False, unique=True,
                                             index=True)

    # Keep a copy of employment_type here for denormalization (in case EmployeeModel changes later)
    employment_type: Mapped[str] = mapped_column(
        SQLAEnum(EmploymentType, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )

    # Financial fields (store canonical values in Rials)
    base_salary_rials: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=24, scale=2), nullable=True,
                                                                 default=None)
    hourly_rate_rials: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=18, scale=2), nullable=True,
                                                                 default=None)
    commission_rate_pct: Mapped[Decimal] = mapped_column(Numeric(precision=6, scale=4), nullable=False,
                                                         default=Decimal("0.0"))

    insured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)  # whether employee is subject to SSO
    marital_status: Mapped[str] = mapped_column(String(20), nullable=False, default="Single")
    children_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    employee: Mapped["EmployeeModel"] = relationship(back_populates="payroll_profile")

    custom_components: Mapped[List["EmployeeCustomPayrollComponentModel"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("employment_type IN ('full_time','part_time','commission')"),
        CheckConstraint("marital_status IN ('Single', 'Married')"),
    )


class EmployeeRoleModel(BasePayroll):
    """
    Stores all possible employee roles.
    New roles can be added dynamically via the admin panel.
    """
    __tablename__ = "employee_roles"

    role_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_name_en: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    role_name_fa: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Reverse relationship
    employees: Mapped[List["EmployeeModel"]] = relationship(
        back_populates="role",
        cascade="all, delete",
    )

    def __repr__(self):
        return f"<Role {self.role_name_en} ({self.role_name_fa})>"


class EmployeeCustomPayrollComponentModel(BasePayroll):
    """A flexible table for custom, employee-specific allowances or deductions."""

    __tablename__ = "employee_custom_payroll_components"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("employee_payroll_profiles.id"), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    value_rials: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=2), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="Allowance")  # 'Allowance' or 'Deduction'

    profile: Mapped["EmployeePayrollProfileModel"] = relationship(back_populates="custom_components")

    __table_args__ = (
        CheckConstraint("type IN ('Allowance', 'Deduction')"),
    )

    __mapper_args__ = {
        "eager_defaults": True,
    }


class SalaryComponentModel(BasePayroll):
    """Defines types of earnings and deductions that can be part of a salary slip.

    These are standard components, not employee-specific custom ones.
    """

    __tablename__ = "salary_components"

    component_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)  # English name for database
    display_name: Mapped[str] = mapped_column(String(100), nullable=True)  # Persian name for UI display
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="Earning")  # 'Earning' or 'Deduction'

    is_taxable_for_income_tax: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_deductible_for_taxable_income: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_base_for_insurance_calculation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    default_rate_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=6, scale=4), nullable=True)

    payroll_details: Mapped[List["PayrollComponentDetailModel"]] = relationship(
        back_populates="salary_component",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("type IN ('Earning', 'Deduction')"),
    )


class PayrollRecordModel(BasePayroll):
    """Stores the summarized payroll results for each employee for a specific pay period.

    This is the main record for a salary slip.
    """

    __tablename__ = "payroll_records"

    payroll_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # Using UUID as PK
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.employee_id"), nullable=False, index=True)

    pay_period_start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    pay_period_end_date: Mapped[Date] = mapped_column(Date, nullable=False)

    base_working_hours_in_period: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    overtime_hours_in_period: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), default=Decimal("0.0"))

    # Monetary amounts stored in Rials
    gross_income_rials: Mapped[Decimal] = mapped_column(Numeric(precision=24, scale=2), nullable=False)
    total_deductions_rials: Mapped[Decimal] = mapped_column(Numeric(precision=24, scale=2), nullable=False)
    taxable_income_rials: Mapped[Decimal] = mapped_column(Numeric(precision=24, scale=2), nullable=False)
    calculated_tax_rials: Mapped[Decimal] = mapped_column(Numeric(precision=24, scale=2), nullable=False)
    calculated_insurance_rials: Mapped[Decimal] = mapped_column(Numeric(precision=24, scale=2), nullable=False)
    net_income_rials: Mapped[Decimal] = mapped_column(Numeric(precision=24, scale=2), nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Draft")  # e.g., 'Draft', 'Finalized', 'Paid'
    calculation_date: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)

    employee: Mapped["EmployeeModel"] = relationship(back_populates="payroll_records")
    component_details: Mapped[List["PayrollComponentDetailModel"]] = relationship(
        back_populates="payroll_record",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("status IN ('Draft', 'Finalized', 'Paid')"),
    )


class PayrollComponentDetailModel(BasePayroll):
    """Stores the specific calculated amount for each salary component within a given payroll record."""

    __tablename__ = "payroll_component_details"

    detail_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payroll_id: Mapped[str] = mapped_column(ForeignKey("payroll_records.payroll_id"), nullable=False, index=True)
    component_id: Mapped[int] = mapped_column(ForeignKey("salary_components.component_id"), nullable=False, index=True)

    amount_rials: Mapped[Decimal] = mapped_column(Numeric(precision=24, scale=2), nullable=False)
    calculation_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # e.g., "20 hours @ 61250 Rials/hr"

    payroll_record: Mapped["PayrollRecordModel"] = relationship(back_populates="component_details")
    salary_component: Mapped["SalaryComponentModel"] = relationship(back_populates="payroll_details")


class TaxBracketModel(BasePayroll):
    """Stores progressive tax brackets for each year. Each row represents a range and its tax rate."""

    __tablename__ = "tax_brackets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    lower_bound_rials: Mapped[Decimal] = mapped_column(Numeric(precision=24, scale=2), nullable=False)
    upper_bound_rials: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=24, scale=2), nullable=True)
    rate: Mapped[Decimal] = mapped_column(Numeric(precision=6, scale=4), nullable=False)  # e.g., 0.10 for 10%


class PayrollRunModel(BasePayroll):
    """
    Represents a single payroll batch — e.g., 'Farvardin 1404 Payroll Run'.
    This groups all employee payslips within a pay period.
    """

    __tablename__ = "payroll_runs"

    payroll_run_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    period_start: Mapped[Date] = mapped_column(Date, nullable=False)
    period_end: Mapped[Date] = mapped_column(Date, nullable=False)
    run_date: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Draft"
    )  # 'Draft', 'Finalized', 'Archived'

    payslips: Mapped[List["PayslipModel"]] = relationship(
        back_populates="payroll_run",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("status IN ('Draft','Finalized','Archived')"),
    )

    def __repr__(self):
        return f"<PayrollRun {self.period_start}–{self.period_end} ({self.status})>"


class PayslipModel(BasePayroll):
    """
    A unified payslip entity — finalized salary record for an employee over a pay period.
    Links to PayrollRunModel and EmployeeModel.

    It mirrors payroll_record data, but represents a legally issued slip (immutable after finalization).
    """

    __tablename__ = "payslips"

    payslip_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    payroll_run_id: Mapped[str] = mapped_column(
        ForeignKey("payroll_runs.payroll_run_id"), index=True, nullable=False
    )
    employee_id: Mapped[str] = mapped_column(
        ForeignKey("employees.employee_id"), index=True, nullable=False
    )

    issue_date: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    period_start: Mapped[Date] = mapped_column(Date, nullable=False)
    period_end: Mapped[Date] = mapped_column(Date, nullable=False)

    gross_income_rials: Mapped[Decimal] = mapped_column(Numeric(24, 2), nullable=False)
    total_deductions_rials: Mapped[Decimal] = mapped_column(Numeric(24, 2), nullable=False)
    net_income_rials: Mapped[Decimal] = mapped_column(Numeric(24, 2), nullable=False)

    payment_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Pending"
    )  # 'Pending', 'Paid', 'Reversed'

    approved_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now, nullable=False)

    payroll_run: Mapped["PayrollRunModel"] = relationship(back_populates="payslips")
    employee: Mapped["EmployeeModel"] = relationship()

    __table_args__ = (
        CheckConstraint("payment_status IN ('Pending','Paid','Reversed')"),
        # Prevent overlapping periods for same employee
        # Note: SQLAlchemy cannot express complex overlap logic easily, enforce via app or trigger
        # but we ensure uniqueness at least:
        CheckConstraint("period_end >= period_start"),
    )

    def __repr__(self):
        return f"<Payslip {self.employee_id} {self.period_start}–{self.period_end}>"


class PayrollAuditLogModel(BasePayroll):
    """
    Audits key payroll actions (payslip creation, update, approval, payment, etc.)
    Each entry is immutable and used for traceability and compliance.
    """

    __tablename__ = "payroll_audit_logs"

    audit_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. 'payslip', 'employee', 'record'
    entity_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)

    action: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. 'create', 'update', 'approve', 'delete'
    performed_by: Mapped[str] = mapped_column(String(100), nullable=True)
    performed_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)

    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Could store JSON or summary text

    def __repr__(self):
        return f"<Audit {self.entity_type}:{self.entity_id} {self.action}>"
