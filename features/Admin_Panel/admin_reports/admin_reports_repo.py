# features/Admin_Panel/admin_reports/admin_reports_repo.py

from sqlalchemy import func, extract, case
from sqlalchemy.orm import Session
from datetime import date, timedelta
import jdatetime
from shared.orm_models.business_models import (IssuedInvoiceModel, InvoiceItemModel, FixedPricesModel, ExpenseModel,
                                               CompanionModel, ServicesModel)


class AdminReportsRepository:
    """
    Stateless repository for fetching and aggregating data for admin financial reports.
    """
    def _get_gregorian_date_range_for_jalali_year(self, year: int) -> tuple[date, date]:
        """Converts a Jalali year into Gregorian start and end dates."""

        # The start of the year is always Farvardin 1st
        start_of_year_j = jdatetime.date(year, 1, 1)

        start_of_next_year_j = jdatetime.date(year + 1, 1, 1)
        end_of_year_j = start_of_next_year_j - timedelta(days=1)

        # Convert the final Jalali dates to Gregorian for the database query
        start_date = start_of_year_j.togregorian()
        end_date = end_of_year_j.togregorian()

        return start_date, end_date

    # --- METHODS FOR YEAR-SPECIFIC DATA ---

    def get_revenue_by_month(self, session: Session, year: int) -> dict:
        """
        Fetches aggregated revenue for each month of a specific Jalali year.
        - For fully paid invoices (status=1), it sums the `final_amount`.
        - For unpaid invoices (status=0), it sums the `advance_payment`.
        """
        start_date, end_date = self._get_gregorian_date_range_for_jalali_year(year)

        # --- MODIFIED: Use a CASE statement for conditional summing ---
        total_revenue_expression = func.sum(
            case(
                (IssuedInvoiceModel.payment_status == 1, IssuedInvoiceModel.final_amount),
                (IssuedInvoiceModel.payment_status == 0, IssuedInvoiceModel.advance_payment),
                else_=0
            )
        ).label('total_revenue')

        revenue_data = session.query(
            extract('month', IssuedInvoiceModel.issue_date).label('gregorian_month'),
            total_revenue_expression
        ).filter(
            # The filter no longer needs to check payment_status, as the CASE handles it.
            IssuedInvoiceModel.issue_date.between(start_date, end_date)
        ).group_by(
            extract('month', IssuedInvoiceModel.issue_date)
        ).all()

        # Return a dictionary mapping the Gregorian month number to the total revenue
        return {row.gregorian_month: row.total_revenue for row in revenue_data}

    def get_total_revenue_for_year(self, session: Session, year: int) -> float:
        start_date, end_date = self._get_gregorian_date_range_for_jalali_year(year)
        total = session.query(
            func.sum(IssuedInvoiceModel.final_amount)
        ).filter(
            IssuedInvoiceModel.payment_status == 1,
            IssuedInvoiceModel.issue_date.between(start_date, end_date)
        ).scalar()
        return total or 0.0

    def get_manual_expenses_by_month(self, session: Session, year: int) -> dict:
        """Fetches expenses like rent and salaries from the Expenses.db."""
        start_date, end_date = self._get_gregorian_date_range_for_jalali_year(year)

        results = session.query(
            extract('month', ExpenseModel.expense_date).label('month'),
            func.sum(ExpenseModel.amount).label('total')
        ).filter(ExpenseModel.expense_date.between(start_date, end_date)).group_by('month').all()
        return {row.month: row.total for row in results}

    def get_invoice_based_expenses_by_month(self, session: Session, year: int) -> dict:
        """Calculates expenses related to seals."""
        start_date, end_date = self._get_gregorian_date_range_for_jalali_year(year)

        # 1. Get seal prices from services.db
        jud_seal_price = session.query(FixedPricesModel.price).filter_by(
            name='judiciary_seal').scalar() or 0
        fa_seal_price = session.query(FixedPricesModel.price).filter_by(
            name='foreign_affairs_seal').scalar() or 0

        # 2. Get monthly counts of seals from invoices.db
        results = (
            session.query(
                extract('month', IssuedInvoiceModel.issue_date).label('month'),
                func.sum(InvoiceItemModel.has_judiciary_seal).label('jud_count'),
                func.sum(InvoiceItemModel.has_foreign_affairs_seal).label('fa_count')
            )
            .join(InvoiceItemModel, IssuedInvoiceModel.invoice_number == InvoiceItemModel.invoice_number)
            .filter(IssuedInvoiceModel.issue_date.between(start_date, end_date))
            .group_by('month')
            .all()
        )

        # 3. Calculate total cost per month
        monthly_costs = {}
        for row in results:
            jud_cost = (row.jud_count or 0) * jud_seal_price
            fa_cost = (row.fa_count or 0) * fa_seal_price
            monthly_costs[row.month] = jud_cost + fa_cost

        # Note: Transportation cost is not included as it's not in the DB.
        return monthly_costs

    # --- METHODS FOR EXCEL EXPORT ---
    def get_detailed_invoices_for_year(self, session: Session, year: int) -> list:
        """Returns a list of all raw IssuedInvoiceModel objects for a given year."""
        start_date, end_date = self._get_gregorian_date_range_for_jalali_year(year)
        return session.query(IssuedInvoiceModel).filter(
            IssuedInvoiceModel.issue_date.between(start_date, end_date)
        ).order_by(IssuedInvoiceModel.issue_date).all()

    def get_detailed_expenses_for_year(self, session: Session, year: int) -> list:
        """Returns a list of all raw ExpenseModel objects for a given year."""
        start_date, end_date = self._get_gregorian_date_range_for_jalali_year(year)
        return session.query(ExpenseModel).filter(
            ExpenseModel.expense_date.between(start_date, end_date)
        ).order_by(ExpenseModel.expense_date).all()

    def get_companion_counts_for_customers(self, session: Session, national_ids: list) -> dict:
        """
        Takes a list of customer national IDs and returns a dictionary
        mapping each ID to their number of companions.
        """
        if not national_ids:
            return {}

        results = session.query(
            CompanionModel.customer_national_id,
            func.count(CompanionModel.id)
        ).filter(
            CompanionModel.customer_national_id.in_(national_ids)
        ).group_by(CompanionModel.customer_national_id).all()

        return {nid: count for nid, count in results}

    # --- METHODS FOR ADVANCED SEARCH ---

    def find_unpaid_invoices_in_range(self, session: Session, start_date: date, end_date: date) -> list:
        """Finds all invoices with outstanding payments issued within a date range."""
        return session.query(IssuedInvoiceModel).filter(
            IssuedInvoiceModel.payment_status == 0,
            IssuedInvoiceModel.issue_date.between(start_date, end_date)
        ).order_by(IssuedInvoiceModel.issue_date.desc()).all()

    def find_invoices_by_document_names(self, session: Session, doc_names: list[str]) -> list:
        """
        Finds all invoices that contain one or more of the specified document names.
        This is a powerful "search by content" query.
        """
        # The .any() clause is a clean way to check for existence in a one-to-many relationship
        return session.query(IssuedInvoiceModel).filter(
            IssuedInvoiceModel.items.any(InvoiceItemModel.service_name.in_(doc_names))
        ).distinct().all()

    def find_frequent_customers(self, session: Session, min_visits: int, start_date: date = None,
                                end_date: date = None) -> list:
        """
        Finds frequent customers, now with an optional date range filter.
        """
        query = session.query(
            IssuedInvoiceModel.name,
            IssuedInvoiceModel.national_id,
            func.count(IssuedInvoiceModel.id).label('visit_count')
        )

        # --- NEW: Add date filter if provided ---
        if start_date and end_date:
            query = query.filter(IssuedInvoiceModel.issue_date.between(start_date, end_date))

        query = query.group_by(
            IssuedInvoiceModel.name,
            IssuedInvoiceModel.national_id
        ).having(
            func.count(IssuedInvoiceModel.id) >= min_visits
        ).order_by(func.count(IssuedInvoiceModel.id).desc())

        return query.all()

    def get_all_service_names(self, session: Session) -> list:
        """Fetches all unique service names from the services table."""
        return session.query(ServicesModel.name).distinct().all()
