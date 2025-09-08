# Admin_Panel/admin_dashboard/admin_dashboard_repo.py

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from datetime import date, timedelta
from shared.orm_models.invoices_models import IssuedInvoiceModel
from shared.orm_models.users_models import LoginLogsModel, UserProfileModel
from shared.orm_models.customer_models import CompanionModel
import jdatetime  # For Jalali date handling


class AdminDashboardRepository:
    """
    Repository class for fetching admin dashboard data.
    """
    def get_revenue_today(self, session: Session) -> float:
        """
        Calculates total revenue from paid invoices issued today.
        """
        today = date.today()
        total = session.query(func.sum(IssuedInvoiceModel.final_amount)).filter(
            IssuedInvoiceModel.payment_status == 1,
            IssuedInvoiceModel.issue_date == today
        ).scalar()
        return total or 0.0

    def get_revenue_this_month(self, session: Session) -> float:
        """
        Calculates total revenue from paid invoices issued this month.
        """
        today = date.today()
        start_of_month = today.replace(day=1)
        total = session.query(func.sum(IssuedInvoiceModel.final_amount)).filter(
            IssuedInvoiceModel.payment_status == 1,
            IssuedInvoiceModel.issue_date >= start_of_month
        ).scalar()
        return total or 0.0

    def get_total_outstanding(self, session: Session) -> float:
        """
        Calculates total outstanding amount from unpaid invoices.
        """
        total = session.query(func.sum(IssuedInvoiceModel.total_amount)).filter(
            IssuedInvoiceModel.payment_status == 0
        ).scalar()
        return total or 0.0

    def get_new_customers_this_month(self, session: Session) -> int:
        """
        Counts distinct customers who had their first invoice issued this month.
        """
        today = date.today()
        start_of_month = today.replace(day=1)
        # Simplified logic: count distinct customers with an invoice this month
        # A more complex version would check if their *first ever* invoice was this month.
        count = session.query(func.count(IssuedInvoiceModel.national_id.distinct())).filter(
            IssuedInvoiceModel.issue_date >= start_of_month
        ).scalar()
        return count or 0

    def get_orders_needing_attention(self, session: Session) -> list:
        """
        Fetches invoices needing attention, now with payment and financial details.
        """
        today = date.today()
        tomorrow = today + timedelta(days=1)

        return session.query(
            IssuedInvoiceModel.invoice_number,
            IssuedInvoiceModel.name,
            IssuedInvoiceModel.delivery_date,
            IssuedInvoiceModel.national_id,  # <-- NEW
            IssuedInvoiceModel.payment_status,  # <-- NEW
            IssuedInvoiceModel.total_amount,  # <-- NEW
            IssuedInvoiceModel.final_amount  # <-- NEW
        ).filter(
            IssuedInvoiceModel.delivery_status != 4,
            IssuedInvoiceModel.delivery_date <= tomorrow
        ).order_by(IssuedInvoiceModel.delivery_date.asc()).limit(10).all()

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

    def _get_jalali_month_range(self) -> tuple[date, date]:
        """Returns the start and end Gregorian dates for the current Jalali month."""
        today_j = jdatetime.date.today()
        start_of_month_j = today_j.replace(day=1)
        next_month_start_j = (start_of_month_j + timedelta(days=31)).replace(day=1)
        end_of_month_j = next_month_start_j - timedelta(days=1)

        return start_of_month_j.togregorian(), end_of_month_j.togregorian()

    # --- Top Translators Query ---
    def get_top_translators_this_month(self, session: Session, limit: int = 3) -> list:
        """
        Finds the top translators by summing the total_items (document count)
        of their invoices for the current JALALI month.
        """
        start_date, end_date = self._get_jalali_month_range()

        return session.query(
            IssuedInvoiceModel.translator,
            func.sum(IssuedInvoiceModel.total_items).label('document_count')
        ).filter(
            IssuedInvoiceModel.issue_date.between(start_date, end_date)
        ).group_by(
            IssuedInvoiceModel.translator
        ).order_by(
            func.sum(IssuedInvoiceModel.total_items).desc()
        ).limit(limit).all()

    # --- Top Clerks Query ---
    def get_top_clerks_this_month(self, session: Session, limit: int = 3) -> list:
        """
        Finds the top clerks by counting invoices for the current JALALI month.
        """
        start_date, end_date = self._get_jalali_month_range()

        return session.query(
            IssuedInvoiceModel.username,
            func.count(IssuedInvoiceModel.id).label('invoice_count')
        ).filter(
            IssuedInvoiceModel.issue_date.between(start_date, end_date),
            IssuedInvoiceModel.username.isnot(None)
        ).group_by(
            IssuedInvoiceModel.username
        ).order_by(
            func.count(IssuedInvoiceModel.id).desc()
        ).limit(limit).all()

    def get_recent_logins(self, session: Session, limit: int = 7) -> list:
        """
        Fetches the latest entries from the LoginLogsModel, joining with UsersModel
        to get the username efficiently.
        """
        return session.query(LoginLogsModel).options(
            joinedload(LoginLogsModel.user) # Eagerly load the related user
        ).order_by(
            LoginLogsModel.id.desc() # Order by ID for most recent entries
        ).limit(limit).all()
