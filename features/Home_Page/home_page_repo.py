# home_page/_repository.py
from typing import List, Optional, Tuple
from datetime import date
from sqlalchemy import func, extract, asc
from sqlalchemy.orm import Session, aliased
import jdatetime  # For Persian date conversion
from shared.utils.persian_tools import to_persian_numbers

# Assuming your ORM models are defined elsewhere and imported
from shared.orm_models.invoices_models import IssuedInvoiceModel, InvoiceItemModel
from shared.orm_models.customer_models import CustomerModel

# Assuming your DTOs are in the models file
from features.Home_Page.home_page_models import DocumentStatistics
from shared.dtos.invoice_dtos import InvoiceItemsDTO, IssuedInvoiceDTO


class HomePageRepository:
    """
    Stateless _repository for home page data operations.
    Requires a session to be passed into each method.
    """

    def get_customer_count(self, session: Session) -> int:
        """Get total number of customers."""
        return session.query(CustomerModel).count()

    def get_total_invoices_count(self, session: Session) -> int:
        """Get total number of invoices."""
        return session.query(IssuedInvoiceModel).count()

    def get_today_invoices_count(self, session: Session, today_date: date) -> int:
        """Get number of invoices issued today."""
        return session.query(IssuedInvoiceModel).filter(
            IssuedInvoiceModel.issue_date == today_date
        ).count()

    def get_invoices_by_delivery_date_range(self, session: Session, start_date: date, end_date: date,
                                            exclude_completed: bool = False) -> List[IssuedInvoiceModel]:
        """Get invoices within a specific delivery date range."""
        query = session.query(IssuedInvoiceModel).filter(
            IssuedInvoiceModel.delivery_date >= start_date,
            IssuedInvoiceModel.delivery_date <= end_date
        )
        if exclude_completed:
            query = query.filter(IssuedInvoiceModel.delivery_status != 4)  # 4 = COLLECTED
        return query.order_by(asc(IssuedInvoiceModel.delivery_date)).all()

    def get_document_statistics(self, session: Session) -> DocumentStatistics:
        """Get document statistics from invoice items considering item quantity."""
        Invoice = aliased(IssuedInvoiceModel)
        Item = aliased(InvoiceItemModel)

        total_docs = session.query(func.sum(Item.quantity)).scalar() or 0
        in_office_docs = session.query(func.sum(Item.quantity)).join(
            Invoice, Item.invoice_number == Invoice.invoice_number
        ).filter(Invoice.delivery_status != 4).scalar() or 0
        delivered_docs = total_docs - in_office_docs

        return DocumentStatistics(
            total_documents=total_docs,
            in_office_documents=in_office_docs,
            delivered_documents=delivered_docs,
        )

    def get_invoice_by_number(self, session: Session, invoice_number: int) -> Optional[IssuedInvoiceModel]:
        """Get a specific invoice ORM model by number."""
        return session.query(IssuedInvoiceModel).filter(
            IssuedInvoiceModel.invoice_number == invoice_number
        ).first()

    def get_customer_by_national_id(self, session: Session, national_id: str) -> Optional[CustomerModel]:
        """Gets a customer ORM model by their national ID."""
        return session.query(CustomerModel).filter(
            CustomerModel.national_id == national_id
        ).first()

    def update_invoice_status(self, session: Session, invoice_number: int, new_status: int,
                              translator: Optional[str] = None) -> bool:
        """Update invoice delivery status and optionally translator."""
        invoice_model = self.get_invoice_by_number(session, invoice_number)
        if not invoice_model:
            return False

        invoice_model.delivery_status = new_status
        if translator is not None:
            invoice_model.translator = translator

        # The _logic layer will be responsible for session.commit()
        return True

    def get_most_repeated_doc(self, session: Session) -> Optional[Tuple[str, int]]:
        """
        Gets the name and total quantity of the most repeated document.
        Returns raw data: (name, total_quantity).
        """
        result = session.query(
            InvoiceItemModel.service,
            func.sum(InvoiceItemModel.quantity).label("total_qty")
        ).group_by(
            InvoiceItemModel.service
        ).order_by(
            func.sum(InvoiceItemModel.quantity).desc()
        ).first()

        return result  # Returns a tuple like ('Passport', 150) or None

    def get_most_repeated_doc_month(self, session: Session) -> Optional[Tuple[str, int, int, int]]:
        """
        Gets the most repeated document in any given month.
        Returns raw data: (name, year, month, total_quantity).
        """
        result = session.query(
            InvoiceItemModel.service,
            extract('year', IssuedInvoiceModel.delivery_date).label("year"),
            extract('month', IssuedInvoiceModel.delivery_date).label("month"),
            func.sum(InvoiceItemModel.quantity).label("total_qty")
        ).join(
            IssuedInvoiceModel, InvoiceItemModel.invoice_number == IssuedInvoiceModel.invoice_number
        ).group_by(
            InvoiceItemModel.service,
            extract('year', IssuedInvoiceModel.delivery_date),
            extract('month', IssuedInvoiceModel.delivery_date)
        ).order_by(
            func.sum(InvoiceItemModel.quantity).desc()
        ).first()

        return result   # Returns a tuple like ('Birth Certificate', 2024, 8, 45) or None

    def update_customer_email(self, session: Session, national_id: str, new_email: str) -> bool:
        """Finds a customer by national ID and updates their email."""
        customer = self.get_customer_by_national_id(session, national_id)
        if customer:
            customer.email = new_email
            return True
        return False
