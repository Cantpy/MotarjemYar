# motarjemyar/wage_calculator/wage_calculator_repo.py

from sqlalchemy.orm import Session, joinedload
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import func
import jdatetime

from shared.database_models.payroll_models import (EmployeeModel, SystemConstantModel, TaxBracketModel,
                                                   PayrollRecordModel, PayrollComponentDetailModel,
                                                   SalaryComponentModel)
from shared.database_models.invoices_models import IssuedInvoiceModel


class WageCalculatorRepository:
    """
    Data access layer for payroll-related operations.
    """
    def get_payroll_run_for_period(self,
                                   session: Session, start_date: date, end_date: date) -> list[PayrollRecordModel]:
        """
        Fetches all saved payroll records where the pay period STARTs within
        the given month. This is a more robust query.
        """
        # Find the start of the next month to create a proper range
        next_month_start_date = (start_date + timedelta(days=32)).replace(day=1)

        return session.query(PayrollRecordModel).options(
            joinedload(PayrollRecordModel.employee)
        ).filter(
            # --- FIX: Check if the start date is within the month's bounds ---
            PayrollRecordModel.pay_period_start_date >= start_date,
            PayrollRecordModel.pay_period_start_date < next_month_start_date
        ).order_by(PayrollRecordModel.employee.has(EmployeeModel.last_name)).all()

    def get_detailed_payslip_by_id(self, session: Session, payroll_id: str) -> PayrollRecordModel | None:
        """Fetches a single, complete payroll record with all its details."""
        return session.query(PayrollRecordModel).options(
            joinedload(PayrollRecordModel.employee),
            joinedload(PayrollRecordModel.component_details).joinedload(PayrollComponentDetailModel.salary_component)
        ).filter(PayrollRecordModel.payroll_id == payroll_id).first()

    def get_all_active_employees(self, session: Session) -> list[EmployeeModel]:
        """Fetches all employees with their payroll profile pre-loaded."""
        return session.query(EmployeeModel).options(joinedload(EmployeeModel.payroll_profile)).all()

    def get_system_constants(self, session: Session, year: int) -> dict[str, Decimal]:
        """Fetches all constants for a given year."""
        results = session.query(SystemConstantModel).filter_by(year=year).all()
        return {item.code: item.value for item in results}

    def get_tax_brackets(self, session: Session, year: int) -> list[TaxBracketModel]:
        """Fetches all tax brackets for a given year, ordered by income level."""
        return session.query(TaxBracketModel).filter_by(year=year).order_by(TaxBracketModel.lower_bound).all()

    def get_translator_performance_rials(self, session: Session, full_name: str, start_date: date, end_date: date) -> Decimal:
        """Calculates total translation price for a translator, converting to Rials."""
        total_tomans = session.query(func.sum(IssuedInvoiceModel.total_translation_price)).filter(
            IssuedInvoiceModel.translator == full_name,
            IssuedInvoiceModel.issue_date.between(start_date, end_date)
        ).scalar() or 0
        return Decimal(total_tomans) * 10

    def get_salary_components_map(self, session: Session) -> dict[str, SalaryComponentModel]:
        """Fetches all standard salary components and returns them as a name-to-object map."""
        results = session.query(SalaryComponentModel).all()
        return {comp.name: comp for comp in results}

    def save_payroll_records_batch(self, session: Session, records: list[PayrollRecordModel]):
        """Saves a batch of new payroll records in a single transaction."""
        session.add_all(records)
        session.commit()
