# features/Home_Page/home_page_repo.py

from typing import List, Optional, Tuple, Dict
from datetime import date
from sqlalchemy import func, extract, asc
from sqlalchemy.orm import Session, aliased

from shared.orm_models.invoices_models import IssuedInvoiceModel, InvoiceItemModel
from shared.orm_models.customer_models import CustomerModel
from shared.orm_models.services_models import ServicesModel
from shared.orm_models.users_models import UsersModel

from features.Home_Page.home_page_models import DocumentStatistics


class HomePageInvoicesRepository:
    """Stateless repository for accessing invoice-related data."""

    def get_total_count(self, session: Session) -> int:
        return session.query(IssuedInvoiceModel).count()

    def get_today_count(self, session: Session, today: date) -> int:
        return session.query(IssuedInvoiceModel).filter(
            IssuedInvoiceModel.issue_date == today
        ).count()

    def get_by_delivery_date_range(
            self, session: Session, start_date: date, end_date: date, exclude_completed: bool = False
    ) -> List[IssuedInvoiceModel]:
        query = session.query(IssuedInvoiceModel).filter(
            IssuedInvoiceModel.delivery_date.between(start_date, end_date)
        )
        if exclude_completed:
            query = query.filter(IssuedInvoiceModel.delivery_status != 4)
        return query.order_by(asc(IssuedInvoiceModel.delivery_date)).all()

    def get_by_number(self, session: Session, invoice_number: str) -> Optional[IssuedInvoiceModel]:
        return session.query(IssuedInvoiceModel).filter(
            IssuedInvoiceModel.invoice_number == invoice_number
        ).first()

    def update_status(self, session: Session, invoice_number: str, new_status: int, translator: Optional[str] = None,
                      new_payment_status: Optional[int] = None) -> bool:
        """
        Updates the delivery status and optionally the payment status of an invoice.
        """
        invoice = self.get_by_number(session, invoice_number)
        if not invoice:
            return False

        invoice.delivery_status = new_status

        if translator:
            invoice.translator = translator

        if new_payment_status is not None:
            invoice.payment_status = new_payment_status

        return True

    def get_document_statistics(self, session: Session) -> DocumentStatistics:
        Invoice = aliased(IssuedInvoiceModel)
        Item = aliased(InvoiceItemModel)

        total_docs = session.query(func.sum(Item.quantity)).scalar() or 0
        in_office_docs = (
                session.query(func.sum(Item.quantity))
                .join(Invoice, Item.invoice_number == Invoice.invoice_number)
                .filter(Invoice.delivery_status != 4)
                .scalar()
                or 0
        )
        delivered_docs = total_docs - in_office_docs

        return DocumentStatistics(total_docs, in_office_docs, delivered_docs)

    def get_most_repeated_doc(self, session: Session) -> Optional[Tuple[int, int]]:
        return (
            session.query(
                InvoiceItemModel.service_id,
                func.sum(InvoiceItemModel.quantity).label("total_qty"),
            )
            .group_by(InvoiceItemModel.service_id)
            .order_by(func.sum(InvoiceItemModel.quantity).desc())
            .first()
        )

    def get_most_repeated_doc_month(self, session: Session) -> Optional[Tuple[int, int, int, int]]:
        return (
            session.query(
                InvoiceItemModel.service_id,
                extract("year", IssuedInvoiceModel.delivery_date).label("year"),
                extract("month", IssuedInvoiceModel.delivery_date).label("month"),
                func.sum(InvoiceItemModel.quantity).label("total_qty"),
            )
            .join(IssuedInvoiceModel, InvoiceItemModel.invoice_number == IssuedInvoiceModel.invoice_number)
            .group_by(
                InvoiceItemModel.service_id,
                extract("year", IssuedInvoiceModel.delivery_date),
                extract("month", IssuedInvoiceModel.delivery_date),
            )
            .order_by(func.sum(InvoiceItemModel.quantity).desc())
            .first()
        )


class HomePageCustomersRepository:
    """Stateless repository for customer data operations."""

    def get_total_count(self, session: Session) -> int:
        return session.query(CustomerModel).count()

    def get_by_national_id(self, session: Session, national_id: str) -> Optional[CustomerModel]:
        return session.query(CustomerModel).filter(CustomerModel.national_id == national_id).first()

    def update_email(self, session: Session, national_id: str, new_email: str) -> bool:
        customer = self.get_by_national_id(session, national_id)
        if customer:
            customer.email = new_email
            return True
        return False


class HomePageServicesRepository:
    """Stateless repository for services-related operations."""

    def get_name_by_id(self, session: Session, service_id: int) -> Optional[str]:
        return session.query(ServicesModel.name).filter(ServicesModel.id == service_id).scalar()

    def get_names_by_ids(self, session: Session, service_ids: List[int]) -> Dict[int, str]:
        if not service_ids:
            return {}
        results = session.query(ServicesModel.id, ServicesModel.name).filter(
            ServicesModel.id.in_(service_ids)
        ).all()
        return {sid: name for sid, name in results}


class HomePageUsersRepository:
    """Stateless repository for user data operations related to the home page."""

    def get_all_translators(self, session: Session) -> List[str]:
        """
        Retrieves the display names of all users with the 'translator' role.
        """
        results = (
            session.query(UsersModel.display_name)
            .filter(UsersModel.role == 'translator')
            .order_by(UsersModel.display_name)
            .all()
        )
        # The query returns a list of tuples, e.g., [('John Doe',), ('Jane Smith',)].
        # We need to flatten it into a simple list of strings.
        return [name for (name,) in results]


class HomePageRepository:
    """Facade to aggregate data from multiple repositories for the dashboard."""

    def __init__(self, invoices_repo: HomePageInvoicesRepository,
                 customers_repo: HomePageCustomersRepository,
                 services_repo: HomePageServicesRepository,
                 users_repo: HomePageUsersRepository):
        self.invoices_repo = invoices_repo
        self.customers_repo = customers_repo
        self.services_repo = services_repo
        self.users_repo = users_repo
