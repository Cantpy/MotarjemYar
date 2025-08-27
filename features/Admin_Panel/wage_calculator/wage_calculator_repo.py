# motarjemyar/wage_calculator/wage_calculator_repo.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import date
from shared.database_models.user_models import UsersModel
from shared.database_models.invoices_models import IssuedInvoiceModel
from shared.database_models.payroll_models import EmployeePayrollProfileModel, LaborLawConstantsModel
import jdatetime  # For Jalali date handling
from datetime import timedelta


class WageCalculatorRepository:
    """
    Repository class for fetching wage calculation related data.
    """

    # --- HELPER METHOD for month-specific date ranges ---
    def _get_gregorian_date_range_for_jalali_month(self, year: int, month: int) -> tuple[date, date]:
        """Converts a Jalali year/month into Gregorian start and end dates."""
        start_date_j = jdatetime.date(year, month, 1)
        end_date_j = (start_date_j + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        return start_date_j.togregorian(), end_date_j.togregorian()

    def get_all_employees(self, session: Session) -> list:
        """Fetches all users with their associated profile data."""
        return session.query(UsersModel).options(joinedload(UsersModel.user_profile)).filter(
            UsersModel.active == 1).all()

    def get_translator_performance(self, session: Session, translator_name: str, start_date: date, end_date: date) -> float:
        """Calculates total translation price for a translator in a date range."""
        total = session.query(func.sum(IssuedInvoiceModel.total_translation_price)).filter(
            IssuedInvoiceModel.translator == translator_name,
            IssuedInvoiceModel.issue_date.between(start_date, end_date)
        ).scalar()
        return total or 0.0

    def get_user_by_id(self, session: Session, user_id: int) -> UsersModel | None:
        """Fetches a single user by their ID, with their profile pre-loaded."""
        return session.query(UsersModel).options(
            joinedload(UsersModel.user_profile)
        ).filter(UsersModel.id == user_id).first()

    def get_clerk_performance(self, session: Session, clerk_username: str, start_date: date, end_date: date) -> int:
        """Counts invoices created by a clerk in a date range."""
        count = session.query(func.count(IssuedInvoiceModel.id)).filter(
            IssuedInvoiceModel.username == clerk_username,
            IssuedInvoiceModel.issue_date.between(start_date, end_date)
        ).scalar()
        return count or 0

    def get_employee_payroll_profile(self, session: Session, user_id: int) -> EmployeePayrollProfileModel | None:
        return session.query(EmployeePayrollProfileModel).filter_by(user_id=user_id).first()

    def get_labor_law_constants(self, session: Session, year: int) -> dict[str, float]:
        """Fetches all constants for a given year and returns them as a dictionary."""
        results = session.query(LaborLawConstantsModel).filter_by(year=year).all()
        return {item.name: item.value for item in results}

    def get_total_invoices_for_month(self, session: Session, year: int, month: int) -> list:
        """
        Fetches all invoices within a specific Jalali month.
        This will be used for multiple calculations.
        """
        start_date, end_date = self._get_gregorian_date_range_for_jalali_month(year, month)
        return session.query(IssuedInvoiceModel).filter(
            IssuedInvoiceModel.issue_date.between(start_date, end_date)
        ).all()
