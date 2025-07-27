"""
Repository layer for home page data access.
Handles all database operations using SQLAlchemy ORM.
"""
from typing import List, Optional, Tuple, Union
from sqlalchemy import (create_engine, Column, Integer, String, Text, Boolean,
                        Date, ForeignKey, func, Index, CheckConstraint, asc, extract)
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship, aliased
from datetime import date
import jdatetime
from shared.utils.number_utils import to_persian_number
from shared.entities.entities import Customer, Service, Invoice, InvoiceItem

from features.Home.home_models import DashboardStats, DocumentStatistics, InvoiceTableRow

Base = declarative_base()


class CustomerModel(Base):
    """SQLAlchemy model for customers."""
    __tablename__ = 'customers'

    national_id = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    phone = Column(Text, nullable=False, unique=True)
    telegram_id = Column(Text)
    email = Column(Text)
    address = Column(Text)
    passport_image = Column(Text)

    __table_args__ = (
        Index('idx_customers_national_id', 'national_id'),
    )


class ServiceModel(Base):
    """SQLAlchemy model for Services."""
    __tablename__ = 'services'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    base_price = Column(Integer)
    dynamic_price_name_1 = Column(Text)
    dynamic_price_1 = Column(Integer)
    dynamic_price_name_2 = Column(Text)
    dynamic_price_2 = Column(Integer)


class FixedPriceModel(Base):
    """SQLAlchemy model for fixed_prices."""
    __tablename__ = 'fixed_prices'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    price = Column(Integer, nullable=False)
    is_default = Column(Boolean, nullable=False)
    label_name = Column(Text)


class OtherServiceModel(Base):
    """SQLAlchemy model for other_services."""
    __tablename__ = 'other_services'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    price = Column(Integer, nullable=False)


class InvoiceItemModel(Base):
    """SQLAlchemy model for invoice_items."""
    __tablename__ = 'invoice_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(Integer, ForeignKey('issued_invoices.invoice_number', ondelete='CASCADE'), nullable=False)
    item_name = Column(Text, nullable=False)
    item_qty = Column(Integer, nullable=False, default=1)
    item_price = Column(Integer, nullable=False)
    officiality = Column(Integer, nullable=False, default=0)
    judiciary_seal = Column(Integer, nullable=False, default=0)
    foreign_affairs_seal = Column(Integer, nullable=False, default=0)
    remarks = Column(Text)

    # Relationships
    invoice = relationship("InvoiceModel", back_populates="items")

    __table_args__ = (
        CheckConstraint('officiality IN (0, 1)', name='chk_invoice_items_officiality'),
        CheckConstraint('judiciary_seal IN (0, 1)', name='chk_invoice_items_judiciary_seal'),
        CheckConstraint('foreign_affairs_seal IN (0, 1)', name='chk_invoice_items_foreign_affairs_seal'),
        Index('idx_invoice_items_foreign', 'foreign_affairs_seal'),
        Index('idx_invoice_items_invoice_id', 'invoice_number'),
        Index('idx_invoice_items_judiciary', 'judiciary_seal'),
        Index('idx_invoice_items_official', 'officiality'),
    )


class InvoiceModel(Base):
    """SQLAlchemy model for issued_invoices."""
    __tablename__ = 'issued_invoices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(Integer, nullable=False, unique=True)
    name = Column(Text, nullable=False)
    national_id = Column(Integer, nullable=False)
    phone = Column(Text, nullable=False)
    issue_date = Column(Date, nullable=False)
    delivery_date = Column(Date, nullable=False)
    translator = Column(Text, nullable=False)
    total_items = Column(Integer)
    total_amount = Column(Integer, nullable=False)
    total_translation_price = Column(Integer, nullable=False)
    advance_payment = Column(Integer, default=0)
    discount_amount = Column(Integer, default=0)
    force_majeure = Column(Integer, default=0)
    final_amount = Column(Integer, nullable=False)
    payment_status = Column(Integer, default=0)
    delivery_status = Column(Integer, default=0)
    total_official_docs_count = Column(Integer, default=0)
    total_unofficial_docs_count = Column(Integer, default=0)
    total_pages_count = Column(Integer, default=0)
    total_judiciary_count = Column(Integer, default=0)
    total_foreign_affairs_count = Column(Integer, default=0)
    total_additional_doc_count = Column(Integer, default=0)
    source_language = Column(Text)
    target_language = Column(Text)
    remarks = Column(Text)
    username = Column(Text)
    pdf_file_path = Column(Text)

    # Relationships
    items = relationship("InvoiceItemModel", back_populates="invoice", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint('payment_status IN (0, 1)', name='chk_issued_invoices_payment_status'),
        CheckConstraint('delivery_status IN (0, 1, 2, 3, 4)', name='chk_issued_invoices_delivery_status'),
        Index('idx_issued_invoices_delivery_date', 'delivery_date'),
        Index('idx_issued_invoices_delivery_status', 'delivery_status'),
        Index('idx_issued_invoices_invoice_status', 'payment_status'),
        Index('idx_issued_invoices_issue_date', 'issue_date'),
        Index('idx_issued_invoices_national_id', 'national_id'),
        Index('idx_issued_invoices_translator', 'translator'),
        Index('idx_issued_invoices_user', 'username'),
    )


class HomePageRepository:
    """Repository for home page data operations."""

    def __init__(self, invoices_db_path: str, customers_db_path: str, services_db_path: str):
        """Initialize repository with database connections."""
        self.invoices_db_path = invoices_db_path
        self.customers_db_path = customers_db_path
        self.services_db_path = services_db_path

        # Create engines
        self.invoice_engine = create_engine(f'sqlite:///{invoices_db_path}')
        self.customer_engine = create_engine(f'sqlite:///{customers_db_path}')
        self.services_engine = create_engine(f'sqlite:///{services_db_path}')

        # Create session makers
        self.invoice_session_maker = sessionmaker(bind=self.invoice_engine)
        self.customer_session_maker = sessionmaker(bind=self.customer_engine)
        self.services_session_maker = sessionmaker(bind=self.services_engine)

    def get_customer_count(self) -> int:
        """Get total number of customers."""
        with self.customer_session_maker() as session:
            return session.query(CustomerModel).count()

    def get_total_invoices_count(self) -> int:
        """Get total number of invoices."""
        with self.invoice_session_maker() as session:
            return session.query(InvoiceModel).count()

    def get_today_invoices_count(self, today_date: date) -> int:
        """Get number of invoices issued today."""
        with self.invoice_session_maker() as session:
            return session.query(InvoiceModel).filter(
                InvoiceModel.issue_date == today_date
            ).count()

    def get_invoices_by_delivery_date_range(self, start_date: date, end_date: date,
                                            exclude_completed: bool = False) -> List[InvoiceModel]:
        """
        Get invoices within a specific delivery date range.

        Args:
            start_date: Start date for the range
            end_date: End date for the range
            exclude_completed: Whether to exclude completed invoices (delivery_status = 4)

        Returns:
            List of InvoiceModel objects
        """
        with self.invoice_session_maker() as session:
            query = session.query(InvoiceModel).filter(
                InvoiceModel.delivery_date >= start_date,
                InvoiceModel.delivery_date <= end_date
            )

            if exclude_completed:
                query = query.filter(InvoiceModel.delivery_status != 4)  # 4 means delivered to the customer

            result = query.order_by(asc(InvoiceModel.delivery_date)).all()
            return result

    def get_document_statistics(self) -> DocumentStatistics:
        """Get document statistics from invoice items considering item quantity."""
        with self.invoice_session_maker() as session:
            Invoice = aliased(InvoiceModel)
            Item = aliased(InvoiceItemModel)

            # Total number of documents (sum of item_qty across all items)
            total_docs = session.query(func.sum(Item.item_qty)).scalar() or 0

            # In-office documents (delivery_status != 4)
            in_office_docs = session.query(func.sum(Item.item_qty)).join(
                Invoice, Item.invoice_number == Invoice.invoice_number
            ).filter(Invoice.delivery_status != 4).scalar() or 0

            # Delivered documents (delivery_status == 4)
            delivered_docs = session.query(func.sum(Item.item_qty)).join(
                Invoice, Item.invoice_number == Invoice.invoice_number
            ).filter(Invoice.delivery_status == 4).scalar() or 0

            return DocumentStatistics(
                total_documents=total_docs,
                in_office_documents=in_office_docs,
                delivered_documents=delivered_docs,
            )

    def get_invoices_for_table(self) -> List[Invoice]:
        """Get all invoices for the table display."""
        invoices = []

        with self.invoice_session_maker() as session:
            invoice_models = session.query(InvoiceModel).all()

            for invoice_model in invoice_models:
                # Get items for this invoice
                items_query = session.query(InvoiceItemModel).filter(
                    InvoiceItemModel.invoice_number == invoice_model.invoice_number
                ).all()

                items = []
                for item_model in items_query:
                    item = InvoiceItem(
                        id=item_model.id,
                        service_name=item_model.item_name,
                        quantity=item_model.item_qty,
                        unit_price=item_model.item_price,
                        total_price=item_model.item_qty * item_model.item_price,
                        officiality=bool(item_model.officiality),
                        judiciary_seal=bool(item_model.judiciary_seal),
                        foreign_affairs_seal=bool(item_model.foreign_affairs_seal),
                        remarks=item_model.remarks
                    )
                    items.append(item)

                invoice = Invoice(
                    id=invoice_model.id,
                    invoice_number=str(invoice_model.invoice_number),
                    name=invoice_model.name,
                    national_id=str(invoice_model.national_id),  # Convert to string for consistency
                    phone=invoice_model.phone,
                    issue_date=invoice_model.issue_date if invoice_model.issue_date else None,
                    delivery_date=invoice_model.delivery_date if invoice_model.delivery_date else None,
                    translator=invoice_model.translator,
                    total_items=len(items),
                    total_amount=invoice_model.total_amount,
                    total_translation_price=invoice_model.total_translation_price,
                    advance_payment=invoice_model.advance_payment,
                    discount_amount=invoice_model.discount_amount,
                    force_majeure=invoice_model.force_majeure,
                    final_amount=invoice_model.final_amount,
                    payment_status=invoice_model.payment_status,
                    delivery_status=invoice_model.delivery_status,
                    total_official_docs_count=invoice_model.total_official_docs_count,
                    total_unofficial_docs_count=invoice_model.total_unofficial_docs_count,
                    total_pages_count=invoice_model.total_pages_count,
                    total_judiciary_count=invoice_model.total_judiciary_count,
                    total_foreign_affairs_count=invoice_model.total_foreign_affairs_count,
                    total_additional_doc_count=invoice_model.total_additional_doc_count,
                    source_language=invoice_model.source_language,
                    target_language=invoice_model.target_language,
                    remarks=invoice_model.remarks,
                    username=invoice_model.username,
                    pdf_file_path=invoice_model.pdf_file_path
                )
                invoices.append(invoice)

        return invoices

    def mark_invoice_as_delivered(self, invoice_number: str) -> bool:
        """Mark an invoice as delivered."""
        with self.invoice_session_maker() as session:
            invoice = session.query(InvoiceModel).filter(
                InvoiceModel.invoice_number == int(invoice_number)
            ).first()

            if invoice:
                invoice.delivery_status = 1
                session.commit()
                return True
            return False

    def get_invoice_by_number(self, invoice_number: int) -> Optional[Invoice]:
        """Get a specific invoice by number."""
        with self.invoice_session_maker() as session:
            invoice_model = session.query(InvoiceModel).filter(
                InvoiceModel.invoice_number == int(invoice_number)
            ).first()

            if not invoice_model:
                return None

            # Get items for this invoice
            items_query = session.query(InvoiceItemModel).filter(
                InvoiceItemModel.invoice_number == int(invoice_number)
            ).all()

            items = []
            for item_model in items_query:
                item = InvoiceItem(
                    id=item_model.id,
                    service_name=item_model.item_name,
                    quantity=item_model.item_qty,
                    unit_price=item_model.item_price,
                    total_price=item_model.item_qty * item_model.item_price,
                    officiality=bool(item_model.officiality),
                    judiciary_seal=bool(item_model.judiciary_seal),
                    foreign_affairs_seal=bool(item_model.foreign_affairs_seal),
                    remarks=item_model.remarks
                )
                items.append(item)

            return Invoice(
                id=invoice_model.id,
                invoice_number=str(invoice_model.invoice_number),
                name=invoice_model.name,
                national_id=str(invoice_model.national_id),  # Convert to string for consistency
                phone=invoice_model.phone,
                issue_date=invoice_model.issue_date.isoformat() if invoice_model.issue_date else "",
                delivery_date=invoice_model.delivery_date.isoformat() if invoice_model.delivery_date else "",
                translator=invoice_model.translator,
                total_items=len(items),
                total_amount=invoice_model.total_amount,
                total_translation_price=invoice_model.total_translation_price,
                advance_payment=invoice_model.advance_payment,
                discount_amount=invoice_model.discount_amount,
                force_majeure=invoice_model.force_majeure,
                final_amount=invoice_model.final_amount,
                payment_status=invoice_model.payment_status,
                delivery_status=invoice_model.delivery_status,
                total_official_docs_count=invoice_model.total_official_docs_count,
                total_unofficial_docs_count=invoice_model.total_unofficial_docs_count,
                total_pages_count=invoice_model.total_pages_count,
                total_judiciary_count=invoice_model.total_judiciary_count,
                total_foreign_affairs_count=invoice_model.total_foreign_affairs_count,
                total_additional_doc_count=invoice_model.total_additional_doc_count,
                source_language=invoice_model.source_language,
                target_language=invoice_model.target_language,
                remarks=invoice_model.remarks,
                username=invoice_model.username,
                pdf_file_path=invoice_model.pdf_file_path
            )

    def get_customers(self) -> List[Customer]:
        """Get all customers."""
        customers = []

        with self.customer_session_maker() as session:
            customer_models = session.query(CustomerModel).all()

            for customer_model in customer_models:
                customer = Customer(
                    national_id=customer_model.national_id,
                    name=customer_model.name,
                    phone=customer_model.phone,
                    telegram_id=customer_model.telegram_id,
                    email=customer_model.email,
                    address=customer_model.address,
                    passport_image=customer_model.passport_image
                )
                customers.append(customer)

        return customers

    def get_customer_by_national_id(self, national_id: str) -> Optional[Customer]:
        """Get a customer by national ID."""
        with self.customer_session_maker() as session:
            customer_model = session.query(CustomerModel).filter(
                CustomerModel.national_id == national_id
            ).first()

            if not customer_model:
                return None

            return Customer(
                national_id=customer_model.national_id,
                name=customer_model.name,
                phone=customer_model.phone,
                telegram_id=customer_model.telegram_id,
                email=customer_model.email,
                address=customer_model.address,
                passport_image=customer_model.passport_image
            )

    def get_services(self) -> List[Service]:
        """Get all services."""
        services = []

        with self.services_session_maker() as session:
            service_models = session.query(ServiceModel).all()

            for service_model in service_models:
                service = Service(
                    id=service_model.id,
                    name=service_model.name,
                    base_price=service_model.base_price,
                    dynamic_price_name_1=service_model.dynamic_price_name_1,
                    dynamic_price_1=service_model.dynamic_price_1,
                    dynamic_price_name_2=service_model.dynamic_price_name_2,
                    dynamic_price_2=service_model.dynamic_price_2
                )
                services.append(service)

        return services

    def get_fixed_prices(self) -> List[dict]:
        """Get all fixed prices."""
        fixed_prices = []

        with self.services_session_maker() as session:
            fixed_price_models = session.query(FixedPriceModel).all()

            for model in fixed_price_models:
                fixed_price = {
                    'id': model.id,
                    'name': model.name,
                    'price': model.price,
                    'is_default': model.is_default,
                    'label_name': model.label_name
                }
                fixed_prices.append(fixed_price)

        return fixed_prices

    def get_other_services(self) -> List[dict]:
        """Get all other services."""
        other_services = []

        with self.services_session_maker() as session:
            other_service_models = session.query(OtherServiceModel).all()

            for model in other_service_models:
                other_service = {
                    'id': model.id,
                    'name': model.name,
                    'price': model.price
                }
                other_services.append(other_service)

        return other_services

    def get_dashboard_stats(self, today_date: date) -> DashboardStats:
        """Get dashboard statistics."""
        # Get customer count from customer database
        with self.customer_session_maker() as session:
            customer_count = session.query(CustomerModel).count()

        # Get invoice statistics and document stats from invoice database
        with self.invoice_session_maker() as session:
            total_invoices = session.query(InvoiceModel).count()
            today_invoices = session.query(InvoiceModel).filter(
                InvoiceModel.issue_date == today_date
            ).count()

            # Get document statistics
            doc_stats = self.get_document_statistics()
            most_repeated_document = self._get_most_repeated_doc()
            most_repeated_document_month = self._get_most_repeated_doc_month()

            return DashboardStats(
                total_customers=customer_count,
                total_invoices=total_invoices,
                today_invoices=today_invoices,
                total_documents=doc_stats.total_documents,
                available_documents=doc_stats.in_office_documents,
                most_repeated_document=most_repeated_document,
                most_repeated_document_month=most_repeated_document_month
            )

    def _get_most_repeated_doc(self):
        """Get most repeated document name (by total quantity, not by row count)"""
        with self.invoice_session_maker() as session:
            most_repeated_document_row = session.query(
                InvoiceItemModel.item_name,
                func.sum(InvoiceItemModel.item_qty).label("total_qty")
            ).group_by(InvoiceItemModel.item_name).order_by(
                func.sum(InvoiceItemModel.item_qty).desc()
            ).first()

            # Process for Persian display
            most_repeated_document = ""
            if most_repeated_document_row:
                name, total_qty = most_repeated_document_row
                most_repeated_document = f"{name} - {to_persian_number(total_qty)}"

            return most_repeated_document

    def _get_most_repeated_doc_month(self):
        """Get the most repeated document in any month (grouped by name+month)"""
        with self.invoice_session_maker() as session:
            most_repeated_document_month_row = session.query(
                InvoiceItemModel.item_name,
                extract('year', InvoiceModel.delivery_date).label("year"),
                extract('month', InvoiceModel.delivery_date).label("month"),
                func.sum(InvoiceItemModel.item_qty).label("total_qty")
            ).join(
                InvoiceModel, InvoiceItemModel.invoice_number == InvoiceModel.invoice_number
            ).group_by(
                InvoiceItemModel.item_name,
                extract('year', InvoiceModel.delivery_date),
                extract('month', InvoiceModel.delivery_date)
            ).order_by(
                func.sum(InvoiceItemModel.item_qty).desc()
            ).first()

            persian_month_names = {
                1: "فروردین",
                2: "اردیبهشت",
                3: "خرداد",
                4: "تیر",
                5: "مرداد",
                6: "شهریور",
                7: "مهر",
                8: "آبان",
                9: "آذر",
                10: "دی",
                11: "بهمن",
                12: "اسفند"
            }

            # Unpack your query result
            name, year, month, total_qty = most_repeated_document_month_row

            # Convert Gregorian to Shamsi date
            g_date = jdatetime.date.fromgregorian(year=int(year), month=int(month), day=1)

            # Get Persian month name
            persian_month = persian_month_names[g_date.month]

            # Format Persian year and digits
            persian_year = to_persian_number(g_date.year)
            persian_total_qty = to_persian_number(total_qty)

            # Compose final string
            most_repeated_document_month = f"{name} - {persian_month} {persian_year} - {persian_total_qty}"

            return most_repeated_document_month

    def create_invoice(self, invoice_data: dict, items_data: List[dict]) -> bool:
        """Create a new invoice with items."""
        with self.invoice_session_maker() as session:
            try:
                # Create invoice
                invoice = InvoiceModel(**invoice_data)
                session.add(invoice)
                session.flush()  # To get the invoice number

                # Create invoice items
                for item_data in items_data:
                    item_data['invoice_number'] = invoice.invoice_number
                    item = InvoiceItemModel(**item_data)
                    session.add(item)

                session.commit()
                return True
            except Exception as e:
                session.rollback()
                return False

    def update_invoice_status(self, invoice_number: int, new_status: int, translator: Optional[str] = None) -> bool:
        """Update invoice delivery status and optionally translator."""
        with self.invoice_session_maker() as session:
            try:
                invoice_model = session.query(InvoiceModel).filter(
                    InvoiceModel.invoice_number == invoice_number
                ).first()

                if not invoice_model:
                    return False

                invoice_model.delivery_status = new_status

                if translator is not None:
                    invoice_model.translator = translator

                session.commit()
                return True

            except Exception as e:
                session.rollback()
                raise e

    # def update_invoice_status(self, invoice_number: str, payment_status: int = None,
    #                           delivery_status: int = None) -> bool:
    #     """Update invoice payment and/or delivery status."""
    #     with self.invoice_session_maker() as session:
    #         invoice = session.query(InvoiceModel).filter(
    #             InvoiceModel.invoice_number == int(invoice_number)
    #         ).first()
    #
    #         if not invoice:
    #             return False
    #
    #         if payment_status is not None:
    #             invoice.payment_status = payment_status
    #         if delivery_status is not None:
    #             invoice.delivery_status = delivery_status
    #
    #         session.commit()
    #         return True

    def get_invoices_by_status(self, delivery_status: int = None,
                              payment_status: int = None) -> List[Invoice]:
        """Get invoices filtered by status."""
        with self.invoice_session_maker() as session:
            query = session.query(InvoiceModel)

            if delivery_status is not None:
                query = query.filter(InvoiceModel.delivery_status == delivery_status)
            if payment_status is not None:
                query = query.filter(InvoiceModel.payment_status == payment_status)

            invoice_models = query.all()

            invoices = []
            for invoice_model in invoice_models:
                # Get items for this invoice
                items_query = session.query(InvoiceItemModel).filter(
                    InvoiceItemModel.invoice_number == invoice_model.invoice_number
                ).all()

                items = []
                for item_model in items_query:
                    item = InvoiceItem(
                        id=item_model.id,
                        service_name=item_model.item_name,
                        quantity=item_model.item_qty,
                        unit_price=item_model.item_price,
                        total_price=item_model.item_qty * item_model.item_price,
                        officiality=bool(item_model.officiality),
                        judiciary_seal=bool(item_model.judiciary_seal),
                        foreign_affairs_seal=bool(item_model.foreign_affairs_seal),
                        remarks=item_model.remarks
                    )
                    items.append(item)

                invoice = Invoice(
                    id=invoice_model.id,
                    invoice_number=str(invoice_model.invoice_number),
                    name=invoice_model.name,
                    national_id=str(invoice_model.national_id),  # Convert to string for consistency
                    phone=invoice_model.phone,
                    issue_date=invoice_model.issue_date.isoformat() if invoice_model.issue_date else "",
                    delivery_date=invoice_model.delivery_date.isoformat() if invoice_model.delivery_date else "",
                    translator=invoice_model.translator,
                    total_items=len(items),
                    total_amount=invoice_model.total_amount,
                    total_translation_price=invoice_model.total_translation_price,
                    advance_payment=invoice_model.advance_payment,
                    discount_amount=invoice_model.discount_amount,
                    force_majeure=invoice_model.force_majeure,
                    final_amount=invoice_model.final_amount,
                    payment_status=invoice_model.payment_status,
                    delivery_status=invoice_model.delivery_status,
                    total_official_docs_count=invoice_model.total_official_docs_count,
                    total_unofficial_docs_count=invoice_model.total_unofficial_docs_count,
                    total_pages_count=invoice_model.total_pages_count,
                    total_judiciary_count=invoice_model.total_judiciary_count,
                    total_foreign_affairs_count=invoice_model.total_foreign_affairs_count,
                    total_additional_doc_count=invoice_model.total_additional_doc_count,
                    source_language=invoice_model.source_language,
                    target_language=invoice_model.target_language,
                    remarks=invoice_model.remarks,
                    username=invoice_model.username,
                    pdf_file_path=invoice_model.pdf_file_path
                )
                invoices.append(invoice)

            return invoices
