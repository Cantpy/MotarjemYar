# repo.py
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from datetime import date, timedelta
from shared.orm_models.invoices_models import BaseInvoices, IssuedInvoiceModel
from shared.orm_models.customer_models import BaseCustomers, CustomerModel
from shared.orm_models.users_models import BaseUsers, UsersModel, LoginLogsModel, UserProfileModel
from typing import List


class ReportsRepo:
    """
    Repository for fetching reports data from the database.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_financial_summary(self, start_date: date, end_date: date) -> dict:
        """ Fetches financial summary data for a given date range. """
        result = self.session.query(
            func.sum(IssuedInvoiceModel.total_amount).label('total_revenue'),
            func.sum(IssuedInvoiceModel.discount_amount).label('total_discount'),
            func.sum(IssuedInvoiceModel.advance_payment).label('total_advance'),
            func.sum(IssuedInvoiceModel.final_amount).label('net_income'),
            func.sum(case((IssuedInvoiceModel.payment_status == 1, 1), else_=0)).label('fully_paid_invoices'),
            func.sum(case((IssuedInvoiceModel.payment_status == 0, 1), else_=0)).label('unpaid_invoices')
        ).filter(
            IssuedInvoiceModel.issue_date.between(start_date, end_date)
        ).first()
        return result._asdict() if result else {}

    def get_revenue_by_translator(self, start_date: date, end_date: date) -> List[dict]:
        """ Fetches aggregated revenue data grouped by translator for a given date range. """
        query = self.session.query(
            IssuedInvoiceModel.translator.label('translator_name'),
            func.sum(IssuedInvoiceModel.final_amount).label('total_revenue'),
            func.count(IssuedInvoiceModel.id).label('invoice_count')
        ).filter(
            IssuedInvoiceModel.issue_date.between(start_date, end_date)
        ).group_by(
            IssuedInvoiceModel.translator
        ).order_by(
            func.sum(IssuedInvoiceModel.final_amount).desc()
        )
        return [row._asdict() for row in query.all()]

    def get_top_customers(self, start_date: date, end_date: date, limit: int = 10) -> List[dict]:
        """ Fetches top customers by total amount spent in a given date range. """
        query = self.session.query(
            CustomerModel.name.label('customer_name'),
            CustomerModel.national_id,
            func.sum(IssuedInvoiceModel.final_amount).label('total_spent'),
            func.count(IssuedInvoiceModel.id).label('invoice_count')
        ).join(
            IssuedInvoiceModel, CustomerModel.national_id == IssuedInvoiceModel.national_id
        ).filter(
            IssuedInvoiceModel.issue_date.between(start_date, end_date)
        ).group_by(
            CustomerModel.name, CustomerModel.national_id
        ).order_by(
            func.sum(IssuedInvoiceModel.final_amount).desc()
        ).limit(limit)
        return [row._asdict() for row in query.all()]

    def get_user_activity(self, start_date: date, end_date: date) -> List[dict]:
        """ Fetches user activity including invoices issued and time spent in the app. """
        # Subquery for invoice counts
        invoice_subquery = self.session.query(
            IssuedInvoiceModel.username,
            func.count(IssuedInvoiceModel.id).label('invoice_count')
        ).filter(
            IssuedInvoiceModel.issue_date.between(start_date, end_date)
        ).group_by(IssuedInvoiceModel.username).subquery()

        # Subquery for time on app
        time_subquery = self.session.query(
            LoginLogsModel.username,
            func.sum(LoginLogsModel.time_on_app).label('total_seconds')
        ).filter(
            # Assuming login_time is stored as string in ISO format.
            # For robustness, this should be a proper DATETIME column.
            func.date(LoginLogsModel.login_time).between(start_date, end_date)
        ).group_by(LoginLogsModel.username).subquery()

        query = self.session.query(
            UsersModel.username,
            UserProfileModel.full_name,
            func.coalesce(invoice_subquery.c.invoice_count, 0).label('invoice_count'),
            func.coalesce(time_subquery.c.total_seconds, 0).label('total_time_on_app_seconds')
        ).outerjoin(
            UserProfileModel, UsersModel.username == UserProfileModel.username
        ).outerjoin(
            invoice_subquery, UsersModel.username == invoice_subquery.c.username
        ).outerjoin(
            time_subquery, UsersModel.username == time_subquery.c.username
        ).order_by(UsersModel.username)

        return [row._asdict() for row in query.all()]
