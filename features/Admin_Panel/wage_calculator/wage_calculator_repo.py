# features/Admin_Panel/wage_calculator/wage_calculator_repo.py

from sqlalchemy.orm import Session, joinedload
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import func, or_
from typing import List

from shared.orm_models.payroll_models import (EmployeeModel, SystemConstantModel, TaxBracketModel,
                                              PayrollRecordModel, PayrollComponentDetailModel,
                                              SalaryComponentModel)
from shared.orm_models.invoices_models import IssuedInvoiceModel
from shared.orm_models.users_models import TranslationOfficeDataModel


class UsersRepository:
    """
    A repository for accessing user-related data.
    """
    def get_translation_office_info(self, users_session: Session) -> list[TranslationOfficeDataModel] | None:
        return users_session.query(TranslationOfficeDataModel).first()


class InvoicesRepository:
    """
    A repository for accessing invoice-related data.
    """
    def get_translator_performance_rials(self, invoices_session: Session, full_name: str, start_date: date,
                                         end_date: date) -> Decimal:
        """Calculates total translation price for a translator, converting to Rials."""
        total_tomans = invoices_session.query(func.sum(IssuedInvoiceModel.total_translation_price)).filter(
            IssuedInvoiceModel.translator == full_name,
            IssuedInvoiceModel.issue_date.between(start_date, end_date)
        ).scalar() or 0
        return Decimal(total_tomans) * 10

    # --- NEW: Method to get detailed invoices for commission calculation ---
    def get_translator_invoices_for_period(self, invoices_session: Session, full_name: str, start_date: date,
                                           end_date: date) -> List[IssuedInvoiceModel]:
        """Fetches all invoices for a translator within a date range to calculate commission details."""
        return invoices_session.query(IssuedInvoiceModel).filter(
            IssuedInvoiceModel.translator == full_name,
            IssuedInvoiceModel.issue_date.between(start_date, end_date)
        ).order_by(IssuedInvoiceModel.issue_date).all()


class PayrollRepository:
    """
    A repository for accessing payroll-related data.
    """
    def get_payroll_run_for_period(self, payroll_session: Session,
                                   start_date: date, end_date: date) -> list[PayrollRecordModel]:
        """
        Fetches all saved payroll records where the pay period STARTs within
        the given month. This is a more robust query.
        """
        next_month_start_date = (start_date + timedelta(days=32)).replace(day=1)

        return payroll_session.query(PayrollRecordModel).options(
            joinedload(PayrollRecordModel.employee)
        ).filter(
            PayrollRecordModel.pay_period_start_date >= start_date,
            PayrollRecordModel.pay_period_start_date < next_month_start_date
        ).order_by(PayrollRecordModel.employee.has(EmployeeModel.last_name)).all()

    def get_detailed_payslip_by_id(self, payroll_session: Session, payroll_id: str) -> PayrollRecordModel | None:
        """Fetches a single, complete payroll record with all its details."""
        return payroll_session.query(PayrollRecordModel).options(
            joinedload(PayrollRecordModel.employee),
            joinedload(PayrollRecordModel.component_details).joinedload(PayrollComponentDetailModel.salary_component)
        ).filter(PayrollRecordModel.payroll_id == payroll_id).first()

    def get_all_active_employees(self, payroll_session: Session) -> list[EmployeeModel]:
        """Fetches all employees who are not terminated."""
        today = date.today()
        return payroll_session.query(EmployeeModel).options(
            joinedload(EmployeeModel.payroll_profile)
        ).filter(
            or_(EmployeeModel.termination_date.is_(None), EmployeeModel.termination_date > today)
        ).all()

    def get_system_constants(self, payroll_session: Session, year: int) -> dict[str, Decimal]:
        """Fetches all constants for a given year."""
        results = payroll_session.query(SystemConstantModel).filter_by(year=year).all()
        return {item.code: item.value for item in results}

    def get_tax_brackets(self, payroll_session: Session, year: int) -> list[TaxBracketModel]:
        """Fetches all tax brackets for a given year, ordered by income level."""
        return (payroll_session.query(TaxBracketModel).filter_by(year=year).
                order_by(TaxBracketModel.lower_bound_rials).all())

    def get_salary_components_map(self, payroll_session: Session) -> dict[str, SalaryComponentModel]:
        """Fetches all standard salary components and returns them as a name-to-object map."""
        results = payroll_session.query(SalaryComponentModel).all()
        return {comp.name: comp for comp in results}

    def get_employee_by_id(self, payroll_session: Session, employee_id: str) -> EmployeeModel | None:
        """Fetches a single employee by their primary employee ID."""
        return payroll_session.query(EmployeeModel).options(
            joinedload(EmployeeModel.payroll_profile)
        ).filter_by(employee_id=employee_id).first()

    def save_payroll_records_batch(self, payroll_session: Session, records: list[PayrollRecordModel]):
        """Saves a batch of new payroll records in a single transaction."""
        payroll_session.add_all(records)
        payroll_session.commit()


class WageCalculatorRepository:
    """
    A repository that aggregates access to users, invoices, and payroll data.
    """
    def __init__(self,
                 users_repository: UsersRepository,
                 invoices_repository: InvoicesRepository,
                 payroll_repository: PayrollRepository):

        self.users_repo = users_repository
        self.invoices_repo = invoices_repository
        self.payroll_repo = payroll_repository
