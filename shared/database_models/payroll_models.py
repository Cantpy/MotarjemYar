# shared/database_models/payroll_models.py

from sqlalchemy import (Text, Integer, Float, Date, CheckConstraint, Index, ForeignKey)
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship

BasePayroll = declarative_base()


class LaborLawConstantsModel(BasePayroll):
    """
    Stores the government-mandated values for a given year.
    This is the "source of truth" for calculations.
    """
    __tablename__ = 'labor_law_constants'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)  # e.g., 'base_salary', 'housing_allowance'
    value: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[str] = mapped_column(Text, default='Allowance')  # 'Allowance' or 'Deduction_Rate'


class EmployeePayrollProfileModel(BasePayroll):
    """Stores the specific payroll setup for each employee."""
    __tablename__ = 'employee_payroll_profiles'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)

    payment_type: Mapped[str] = mapped_column(Text, default='Fixed')
    custom_base_salary: Mapped[int] = mapped_column(Integer, default=0)
    commission_rate: Mapped[float] = mapped_column(Float, default=0.0)
    per_invoice_rate: Mapped[int] = mapped_column(Integer, default=0)

    # --- NEW SEMI-PERMANENT FIELDS ---
    marital_status: Mapped[str] = mapped_column(Text, default='Single')  # 'Single' or 'Married'
    children_count: Mapped[int] = mapped_column(Integer, default=0)

    # ... (relationship to custom components)
    __table_args__ = (
        CheckConstraint("payment_type IN ('Fixed', 'Commission')"),
        CheckConstraint("marital_status IN ('Single', 'Married')"),
    )


class EmployeePayrollComponentModel(BasePayroll):
    """A flexible table for custom, employee-specific allowances or deductions."""
    __tablename__ = 'employee_payroll_components'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey('employee_payroll_profiles.id'))

    name: Mapped[str] = mapped_column(Text, nullable=False)  # e.g., "Bonus", "Loan Deduction"
    value: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[str] = mapped_column(Text, default='Allowance')  # 'Allowance' or 'Deduction'

    profile: Mapped["EmployeePayrollProfileModel"] = relationship(back_populates="custom_components")
