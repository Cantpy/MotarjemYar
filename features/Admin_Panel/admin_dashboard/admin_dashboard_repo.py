# Admin_Panel/admin_dashboard/admin_dashboard_repo.py

from sqlalchemy import func, cast, Date
from sqlalchemy.orm import Session, joinedload
from datetime import date, timedelta, datetime, time
from shared.orm_models.invoices_models import IssuedInvoiceModel
from shared.orm_models.users_models import LoginLogsModel
from shared.orm_models.customer_models import CompanionModel
import jdatetime


class AdminDashboardRepository:
    """
    Stateless _repository class for fetching admin dashboard data.
    """
    def get_revenue_today(self, session: Session) -> float:
        """
        Calculates total revenue received today (in UTC).
        This includes:
        1. The final_amount of invoices fully paid today.
        2. The advance_payment of new invoices issued today that are not yet fully paid.
        """

        today_utc = datetime.utcnow().date()
        start_of_today_utc = datetime.combine(today_utc, time.min)
        end_of_today_utc = datetime.combine(today_utc, time.max)

        # 1. Revenue from fully paid invoices today
        paid_today_total = session.query(func.sum(IssuedInvoiceModel.final_amount)).filter(
            IssuedInvoiceModel.payment_date.between(start_of_today_utc, end_of_today_utc)
        ).scalar() or 0.0

        # 2. Revenue from advance payments on new unpaid invoices issued today
        advance_today_total = session.query(func.sum(IssuedInvoiceModel.advance_payment)).filter(
            IssuedInvoiceModel.issue_date.between(start_of_today_utc, end_of_today_utc),
            IssuedInvoiceModel.payment_status == 0
        ).scalar() or 0.0

        return paid_today_total + advance_today_total

    def get_revenue_this_month(self, session: Session) -> float:
        """
        Calculates total revenue received this month (in UTC).
        This includes:
        1. The final_amount of invoices fully paid this month.
        2. The advance_payment of new invoices issued this month that are not yet fully paid.
        """
        today_utc = datetime.utcnow().date()
        start_of_month_utc = datetime.combine(today_utc.replace(day=1), time.min)

        # 1. Revenue from fully paid invoices this month
        paid_this_month_total = session.query(func.sum(IssuedInvoiceModel.final_amount)).filter(
            IssuedInvoiceModel.payment_date >= start_of_month_utc
        ).scalar() or 0.0

        # 2. Revenue from advance payments on new unpaid invoices issued this month
        advance_this_month_total = session.query(func.sum(IssuedInvoiceModel.advance_payment)).filter(
            IssuedInvoiceModel.issue_date >= start_of_month_utc,
            IssuedInvoiceModel.payment_status == 0
        ).scalar() or 0.0

        return paid_this_month_total + advance_this_month_total

    def get_total_outstanding(self, session: Session) -> float:
        """
        Calculates total outstanding amount from unpaid invoices.
        This is the sum of (final_amount - advance_payment) for all unpaid invoices.
        """
        total = session.query(func.sum(IssuedInvoiceModel.final_amount - IssuedInvoiceModel.advance_payment)).filter(
            IssuedInvoiceModel.payment_status == 0
        ).scalar()
        return total or 0.0

    def get_new_customers_this_month(self, session: Session) -> int:
        """
        Counts distinct customers who had their first invoice issued this month.
        """
        today = date.today()
        start_of_month = today.replace(day=1)
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
            IssuedInvoiceModel.national_id,
            IssuedInvoiceModel.payment_status,
            IssuedInvoiceModel.total_amount,
            IssuedInvoiceModel.final_amount,
            IssuedInvoiceModel.advance_payment
        ).filter(
            IssuedInvoiceModel.delivery_status != 4,
            cast(IssuedInvoiceModel.delivery_date, Date) <= tomorrow
        ).order_by(IssuedInvoiceModel.delivery_date.asc()).limit(10).all()

    def get_unpaid_collected_invoices(self, session: Session) -> list:
        """
        Fetches invoices that have been collected but not paid.
        """
        return session.query(
            IssuedInvoiceModel.invoice_number,
            IssuedInvoiceModel.name,
            IssuedInvoiceModel.phone,
            IssuedInvoiceModel.final_amount,
            IssuedInvoiceModel.collection_date
        ).filter(
            IssuedInvoiceModel.delivery_status == 4,
            IssuedInvoiceModel.payment_status == 0
        ).order_by(IssuedInvoiceModel.collection_date.asc()).all()

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
            joinedload(LoginLogsModel.user)
        ).order_by(
            LoginLogsModel.id.desc()
        ).limit(limit).all()
