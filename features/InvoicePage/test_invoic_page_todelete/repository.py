from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Date, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from features.InvoicePage.test_invoic_page_todelete.models import (
    Customer, Service, FixedPrice, OtherService, Invoice, InvoiceItem,
    PaymentStatus, DeliveryStatus, CustomerSearchCriteria, InvoiceSearchCriteria
)

Base = declarative_base()


# SQLAlchemy ORM Models
class CustomerORM(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True)
    national_id = Column(String(10), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(15), unique=True, nullable=False)
    address = Column(Text, nullable=False)
    telegram_id = Column(String(255))
    email = Column(String(255))
    passport_image = Column(String(500))


class ServiceORM(Base):
    __tablename__ = 'services'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    base_price = Column(Integer, nullable=False)
    dynamic_price_1 = Column(Integer)
    dynamic_price_2 = Column(Integer)
    dynamic_price_name_1 = Column(String(255))
    dynamic_price_name_2 = Column(String(255))


class FixedPriceORM(Base):
    __tablename__ = 'fixed_prices'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    price = Column(Integer, nullable=False)


class OtherServiceORM(Base):
    __tablename__ = 'other_services'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)


class InvoiceORM(Base):
    __tablename__ = 'invoices'

    id = Column(Integer, primary_key=True)
    invoice_number = Column(Integer, unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    national_id = Column(String(10), nullable=False)
    phone = Column(String(15), nullable=False)
    issue_date = Column(Date, nullable=False)
    delivery_date = Column(Date, nullable=False)
    translator = Column(String(255), nullable=False)
    total_amount = Column(Integer, default=0)
    total_translation_price = Column(Integer, default=0)
    advance_payment = Column(Integer, default=0)
    discount_amount = Column(Integer, default=0)
    force_majeure = Column(Integer, default=0)
    final_amount = Column(Integer, default=0)
    source_language = Column(String(100))
    target_language = Column(String(100))
    remarks = Column(Text)
    username = Column(String(255))
    payment_status = Column(Integer, default=0)
    delivery_status = Column(Integer, default=0)
    total_official_docs_count = Column(Integer, default=0)
    total_unofficial_docs_count = Column(Integer, default=0)
    total_pages_count = Column(Integer, default=0)
    total_judiciary_count = Column(Integer, default=0)
    total_foreign_affairs_count = Column(Integer, default=0)
    total_additional_doc_count = Column(Integer, default=0)

    items = relationship("InvoiceItemORM", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItemORM(Base):
    __tablename__ = 'invoice_items'

    id = Column(Integer, primary_key=True)
    invoice_number = Column(Integer, ForeignKey('invoices.invoice_number'), nullable=False)
    item_name = Column(String(255), nullable=False)
    item_qty = Column(Integer, nullable=False)
    item_price = Column(Integer, nullable=False)
    officiality = Column(Integer, default=0)
    judiciary_seal = Column(Integer, default=0)
    foreign_affairs_seal = Column(Integer, default=0)
    remarks = Column(Text)

    invoice = relationship("InvoiceORM", back_populates="items")


# Repository Interfaces
class InvoiceRepository(ABC):
    @abstractmethod
    def _item_orm_to_domain(self, orm_item: InvoiceItemORM) -> InvoiceItem:
        """Convert ORM item model to domain model."""
        return InvoiceItem(
            id=orm_item.id,
            invoice_number=orm_item.invoice_number,
            item_name=orm_item.item_name,
            item_qty=orm_item.item_qty,
            item_price=orm_item.item_price,
            officiality=orm_item.officiality,
            judiciary_seal=orm_item.judiciary_seal,
            foreign_affairs_seal=orm_item.foreign_affairs_seal,
            remarks=orm_item.remarks
        )

    def _domain_to_orm(self, invoice: Invoice) -> InvoiceORM:
        """Convert domain model to ORM model."""
        orm_invoice = InvoiceORM(
            id=invoice.id,
            invoice_number=invoice.invoice_number,
            name=invoice.name,
            national_id=invoice.national_id,
            phone=invoice.phone,
            issue_date=invoice.issue_date,
            delivery_date=invoice.delivery_date,
            translator=invoice.translator,
            total_amount=invoice.total_amount,
            total_translation_price=invoice.total_translation_price,
            advance_payment=invoice.advance_payment,
            discount_amount=invoice.discount_amount,
            force_majeure=invoice.force_majeure,
            final_amount=invoice.final_amount,
            source_language=invoice.source_language,
            target_language=invoice.target_language,
            remarks=invoice.remarks,
            username=invoice.username,
            payment_status=invoice.payment_status.value,
            delivery_status=invoice.delivery_status.value,
            total_official_docs_count=invoice.total_official_docs_count,
            total_unofficial_docs_count=invoice.total_unofficial_docs_count,
            total_pages_count=invoice.total_pages_count,
            total_judiciary_count=invoice.total_judiciary_count,
            total_foreign_affairs_count=invoice.total_foreign_affairs_count,
            total_additional_doc_count=invoice.total_additional_doc_count
        )

        # Convert items
        orm_invoice.items = [self._item_domain_to_orm(item) for item in invoice.items]
        return orm_invoice

    def _item_domain_to_orm(self, item: InvoiceItem) -> InvoiceItemORM:
        """Convert domain item model to ORM model."""
        return InvoiceItemORM(
            id=item.id,
            invoice_number=item.invoice_number,
            item_name=item.item_name,
            item_qty=item.item_qty,
            item_price=item.item_price,
            officiality=item.officiality,
            judiciary_seal=item.judiciary_seal,
            foreign_affairs_seal=item.foreign_affairs_seal,
            remarks=item.remarks
        )

    def get_all(self) -> List[Invoice]:
        with self.db_manager.get_invoices_session() as session:
            orm_invoices = session.query(InvoiceORM).all()
            return [self._orm_to_domain(i) for i in orm_invoices]

    def get_by_number(self, invoice_number: int) -> Optional[Invoice]:
        with self.db_manager.get_invoices_session() as session:
            orm_invoice = session.query(InvoiceORM).filter(InvoiceORM.invoice_number == invoice_number).first()
            return self._orm_to_domain(orm_invoice) if orm_invoice else None

    def get_next_invoice_number(self) -> int:
        with self.db_manager.get_invoices_session() as session:
            last_invoice = session.query(InvoiceORM).order_by(InvoiceORM.invoice_number.desc()).first()
            return last_invoice.invoice_number + 1 if last_invoice else 1000

    def save(self, invoice: Invoice) -> Invoice:
        with self.db_manager.get_invoices_session() as session:
            if invoice.id:
                # Update existing
                orm_invoice = session.query(InvoiceORM).filter(InvoiceORM.id == invoice.id).first()
                if orm_invoice:
                    # Update invoice fields
                    orm_invoice.name = invoice.name
                    orm_invoice.national_id = invoice.national_id
                    orm_invoice.phone = invoice.phone
                    orm_invoice.issue_date = invoice.issue_date
                    orm_invoice.delivery_date = invoice.delivery_date
                    orm_invoice.translator = invoice.translator
                    orm_invoice.total_amount = invoice.total_amount
                    orm_invoice.total_translation_price = invoice.total_translation_price
                    orm_invoice.advance_payment = invoice.advance_payment
                    orm_invoice.discount_amount = invoice.discount_amount
                    orm_invoice.force_majeure = invoice.force_majeure
                    orm_invoice.final_amount = invoice.final_amount
                    orm_invoice.source_language = invoice.source_language
                    orm_invoice.target_language = invoice.target_language
                    orm_invoice.remarks = invoice.remarks
                    orm_invoice.username = invoice.username
                    orm_invoice.payment_status = invoice.payment_status.value
                    orm_invoice.delivery_status = invoice.delivery_status.value
                    orm_invoice.total_official_docs_count = invoice.total_official_docs_count
                    orm_invoice.total_unofficial_docs_count = invoice.total_unofficial_docs_count
                    orm_invoice.total_pages_count = invoice.total_pages_count
                    orm_invoice.total_judiciary_count = invoice.total_judiciary_count
                    orm_invoice.total_foreign_affairs_count = invoice.total_foreign_affairs_count
                    orm_invoice.total_additional_doc_count = invoice.total_additional_doc_count

                    # Update items (cascade will handle deletion)
                    orm_invoice.items = [self._item_domain_to_orm(item) for item in invoice.items]
                else:
                    raise ValueError("Invoice not found")
            else:
                # Create new
                orm_invoice = self._domain_to_orm(invoice)
                session.add(orm_invoice)

            session.flush()  # To get the ID
            return self._orm_to_domain(orm_invoice)

    def delete(self, invoice_id: int) -> bool:
        with self.db_manager.get_invoices_session() as session:
            orm_invoice = session.query(InvoiceORM).filter(InvoiceORM.id == invoice_id).first()
            if orm_invoice:
                session.delete(orm_invoice)
                return True
            return False

    def search(self, criteria: InvoiceSearchCriteria) -> List[Invoice]:
        with self.db_manager.get_invoices_session() as session:
            query = session.query(InvoiceORM)

            if criteria.invoice_number:
                query = query.filter(InvoiceORM.invoice_number == criteria.invoice_number)
            if criteria.customer_name:
                query = query.filter(InvoiceORM.name.ilike(f"%{criteria.customer_name}%"))
            if criteria.national_id:
                query = query.filter(InvoiceORM.national_id == criteria.national_id)
            if criteria.payment_status is not None:
                query = query.filter(InvoiceORM.payment_status == criteria.payment_status.value)
            if criteria.delivery_status is not None:
                query = query.filter(InvoiceORM.delivery_status == criteria.delivery_status.value)
            if criteria.date_from:
                query = query.filter(InvoiceORM.issue_date >= criteria.date_from)
            if criteria.date_to:
                query = query.filter(InvoiceORM.issue_date <= criteria.date_to)

            orm_invoices = query.all()
            return [self._orm_to_domain(i) for i in orm_invoices]

    def get_unpaid_invoices(self) -> List[Invoice]:
        with self.db_manager.get_invoices_session() as session:
            orm_invoices = session.query(InvoiceORM).filter(
                InvoiceORM.payment_status == PaymentStatus.UNPAID.value).all()
            return [self._orm_to_domain(i) for i in orm_invoices]

    def get_pending_delivery_invoices(self) -> List[Invoice]:
        with self.db_manager.get_invoices_session() as session:
            pending_statuses = [
                DeliveryStatus.PENDING.value,
                DeliveryStatus.IN_PROGRESS.value,
                DeliveryStatus.READY.value,
                DeliveryStatus.QUALITY_CHECK.value
            ]
            orm_invoices = session.query(InvoiceORM).filter(InvoiceORM.delivery_status.in_(pending_statuses)).all()
            return [self._orm_to_domain(i) for i in orm_invoices]


# Error translation utility
SQLITE_ERROR_TRANSLATIONS = {
    "UNIQUE constraint failed": "خطای یکتایی: داده تکراری مجاز نیست.",
    "NOT NULL constraint failed": "خطای مقدار خالی: این فیلد اجباری است.",
    "FOREIGN KEY constraint failed": "خطای کلید خارجی: داده مرتبط وجود ندارد.",
    "no such table": "جدول مورد نظر وجود ندارد.",
    "no such column": "ستون مورد نظر وجود ندارد.",
    "database is locked": "پایگاه داده قفل شده است. لطفاً بعداً تلاش کنید.",
    "syntax error": "خطای دستوری در کوئری SQL.",
    "near": "خطای دستوری در بخشی از کوئری",
    "permission denied": "دسترسی به پایگاه داده مجاز نیست.",
    "disk I/O error": "خطای خواندن/نوشتن روی دیسک.",
}


def translate_sqlite_error(error) -> str:
    """Translate SQLite error messages to Persian."""
    error_str = str(error)
    for key, translation in SQLITE_ERROR_TRANSLATIONS.items():
        if key in error_str:
            return translation
    return f"خطای ناشناخته پایگاه داده: {error_str}"


class ICustomerRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[Customer]:
        pass

    @abstractmethod
    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        pass

    @abstractmethod
    def get_by_national_id(self, national_id: str) -> Optional[Customer]:
        pass

    @abstractmethod
    def get_by_phone(self, phone: str) -> Optional[Customer]:
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Customer]:
        pass

    @abstractmethod
    def search(self, criteria: CustomerSearchCriteria) -> List[Customer]:
        pass

    @abstractmethod
    def save(self, customer: Customer) -> Customer:
        pass

    @abstractmethod
    def delete(self, customer_id: int) -> bool:
        pass

    @abstractmethod
    def get_suggestions(self, field: str) -> List[str]:
        pass


class IServiceRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[Service]:
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Service]:
        pass

    @abstractmethod
    def get_names(self) -> List[str]:
        pass

    @abstractmethod
    def save(self, service: Service) -> Service:
        pass


class IInvoiceRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[Invoice]:
        pass

    @abstractmethod
    def get_by_number(self, invoice_number: int) -> Optional[Invoice]:
        pass

    @abstractmethod
    def get_next_invoice_number(self) -> int:
        pass

    @abstractmethod
    def save(self, invoice: Invoice) -> Invoice:
        pass

    @abstractmethod
    def delete(self, invoice_id: int) -> bool:
        pass

    @abstractmethod
    def search(self, criteria: InvoiceSearchCriteria) -> List[Invoice]:
        pass

    @abstractmethod
    def get_unpaid_invoices(self) -> List[Invoice]:
        pass

    @abstractmethod
    def get_pending_delivery_invoices(self) -> List[Invoice]:
        pass


# Repository Implementations
class DatabaseManager:
    """Database connection manager."""

    def __init__(self, customers_db_path: str, invoices_db_path: str, services_db_path: str):
        self.customers_engine = create_engine(f"sqlite:///{customers_db_path}")
        self.invoices_engine = create_engine(f"sqlite:///{invoices_db_path}")
        self.services_engine = create_engine(f"sqlite:///{services_db_path}")

        self.customers_session_factory = sessionmaker(bind=self.customers_engine)
        self.invoices_session_factory = sessionmaker(bind=self.invoices_engine)
        self.services_session_factory = sessionmaker(bind=self.services_engine)

        # Create tables
        Base.metadata.create_all(self.customers_engine)
        Base.metadata.create_all(self.invoices_engine)
        Base.metadata.create_all(self.services_engine)

    @contextmanager
    def get_customers_session(self) -> Session:
        session = self.customers_session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def get_invoices_session(self) -> Session:
        session = self.invoices_session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def get_services_session(self) -> Session:
        session = self.services_session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


class SQLAlchemyCustomerRepository(ICustomerRepository):
    """SQLAlchemy implementation of customer repository."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def _orm_to_domain(self, orm_customer: CustomerORM) -> Customer:
        """Convert ORM model to domain model."""
        return Customer(
            id=orm_customer.id,
            national_id=orm_customer.national_id,
            name=orm_customer.name,
            phone=orm_customer.phone,
            address=orm_customer.address,
            telegram_id=orm_customer.telegram_id,
            email=orm_customer.email,
            passport_image=orm_customer.passport_image
        )

    def _domain_to_orm(self, customer: Customer) -> CustomerORM:
        """Convert domain model to ORM model."""
        return CustomerORM(
            id=customer.id,
            national_id=customer.national_id,
            name=customer.name,
            phone=customer.phone,
            address=customer.address,
            telegram_id=customer.telegram_id,
            email=customer.email,
            passport_image=customer.passport_image
        )

    def get_all(self) -> List[Customer]:
        with self.db_manager.get_customers_session() as session:
            orm_customers = session.query(CustomerORM).all()
            return [self._orm_to_domain(c) for c in orm_customers]

    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        with self.db_manager.get_customers_session() as session:
            orm_customer = session.query(CustomerORM).filter(CustomerORM.id == customer_id).first()
            return self._orm_to_domain(orm_customer) if orm_customer else None

    def get_by_national_id(self, national_id: str) -> Optional[Customer]:
        with self.db_manager.get_customers_session() as session:
            orm_customer = session.query(CustomerORM).filter(CustomerORM.national_id == national_id).first()
            return self._orm_to_domain(orm_customer) if orm_customer else None

    def get_by_phone(self, phone: str) -> Optional[Customer]:
        with self.db_manager.get_customers_session() as session:
            orm_customer = session.query(CustomerORM).filter(CustomerORM.phone == phone).first()
            return self._orm_to_domain(orm_customer) if orm_customer else None

    def get_by_name(self, name: str) -> Optional[Customer]:
        with self.db_manager.get_customers_session() as session:
            orm_customer = session.query(CustomerORM).filter(CustomerORM.name == name).first()
            return self._orm_to_domain(orm_customer) if orm_customer else None

    def search(self, criteria: CustomerSearchCriteria) -> List[Customer]:
        with self.db_manager.get_customers_session() as session:
            query = session.query(CustomerORM)

            if criteria.name:
                query = query.filter(CustomerORM.name.ilike(f"%{criteria.name}%"))
            if criteria.phone:
                query = query.filter(CustomerORM.phone.ilike(f"%{criteria.phone}%"))
            if criteria.national_id:
                query = query.filter(CustomerORM.national_id.ilike(f"%{criteria.national_id}%"))

            orm_customers = query.all()
            return [self._orm_to_domain(c) for c in orm_customers]

    def save(self, customer: Customer) -> Customer:
        with self.db_manager.get_customers_session() as session:
            if customer.id:
                # Update existing
                orm_customer = session.query(CustomerORM).filter(CustomerORM.id == customer.id).first()
                if orm_customer:
                    orm_customer.national_id = customer.national_id
                    orm_customer.name = customer.name
                    orm_customer.phone = customer.phone
                    orm_customer.address = customer.address
                    orm_customer.telegram_id = customer.telegram_id
                    orm_customer.email = customer.email
                    orm_customer.passport_image = customer.passport_image
                else:
                    raise ValueError("CustomerModel not found")
            else:
                # Create new
                orm_customer = self._domain_to_orm(customer)
                session.add(orm_customer)

            session.flush()  # To get the ID
            return self._orm_to_domain(orm_customer)

    def delete(self, customer_id: int) -> bool:
        with self.db_manager.get_customers_session() as session:
            orm_customer = session.query(CustomerORM).filter(CustomerORM.id == customer_id).first()
            if orm_customer:
                session.delete(orm_customer)
                return True
            return False

    def get_suggestions(self, field: str) -> List[str]:
        with self.db_manager.get_customers_session() as session:
            if field == "name":
                results = session.query(CustomerORM.name).distinct().all()
            elif field == "phone":
                results = session.query(CustomerORM.phone).distinct().all()
            elif field == "national_id":
                results = session.query(CustomerORM.national_id).distinct().all()
            else:
                return []

            return [result[0] for result in results if result[0]]


class SQLAlchemyServiceRepository(IServiceRepository):
    """SQLAlchemy implementation of service repository."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def _orm_to_domain(self, orm_service: ServiceORM) -> Service:
        """Convert ORM model to domain model."""
        return Service(
            id=orm_service.id,
            name=orm_service.name,
            base_price=orm_service.base_price,
            dynamic_price_1=orm_service.dynamic_price_1,
            dynamic_price_2=orm_service.dynamic_price_2,
            dynamic_price_name_1=orm_service.dynamic_price_name_1,
            dynamic_price_name_2=orm_service.dynamic_price_name_2
        )

    def get_all(self) -> List[Service]:
        with self.db_manager.get_services_session() as session:
            orm_services = session.query(ServiceORM).all()
            return [self._orm_to_domain(s) for s in orm_services]

    def get_by_name(self, name: str) -> Optional[Service]:
        with self.db_manager.get_services_session() as session:
            orm_service = session.query(ServiceORM).filter(ServiceORM.name == name).first()
            return self._orm_to_domain(orm_service) if orm_service else None

    def get_names(self) -> List[str]:
        with self.db_manager.get_services_session() as session:
            results = session.query(ServiceORM.name).all()
            return [result[0] for result in results]

    def save(self, service: Service) -> Service:
        with self.db_manager.get_services_session() as session:
            if service.id:
                # Update existing
                orm_service = session.query(ServiceORM).filter(ServiceORM.id == service.id).first()
                if orm_service:
                    orm_service.name = service.name
                    orm_service.base_price = service.base_price
                    orm_service.dynamic_price_1 = service.dynamic_price_1
                    orm_service.dynamic_price_2 = service.dynamic_price_2
                    orm_service.dynamic_price_name_1 = service.dynamic_price_name_1
                    orm_service.dynamic_price_name_2 = service.dynamic_price_name_2
                else:
                    raise ValueError("ServicesModel not found")
            else:
                # Create new
                orm_service = ServiceORM(
                    name=service.name,
                    base_price=service.base_price,
                    dynamic_price_1=service.dynamic_price_1,
                    dynamic_price_2=service.dynamic_price_2,
                    dynamic_price_name_1=service.dynamic_price_name_1,
                    dynamic_price_name_2=service.dynamic_price_name_2
                )
                session.add(orm_service)

            session.flush()  # To get the ID
            return self._orm_to_domain(orm_service)


class SQLAlchemyInvoiceRepository(IInvoiceRepository):
    """SQLAlchemy implementation of invoice repository."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def _orm_to_domain(self, orm_invoice: InvoiceORM) -> Invoice:
        """Convert ORM model to domain model."""
        items = [self._item_orm_to_domain(item) for item in orm_invoice.items]

        return Invoice(
            id=orm_invoice.id,
            invoice_number=orm_invoice.invoice_number,
            name=orm_invoice.name,
            national_id=orm_invoice.national_id,
            phone=orm_invoice.phone,
            issue_date=orm_invoice.issue_date,
            delivery_date=orm_invoice.delivery_date,
            translator=orm_invoice.translator,
            total_amount=orm_invoice.total_amount,
            total_translation_price=orm_invoice.total_translation_price,
            advance_payment=orm_invoice.advance_payment,
            discount_amount=orm_invoice.discount_amount,
            force_majeure=orm_invoice.force_majeure,
            final_amount=orm_invoice.final_amount,
            source_language=orm_invoice.source_language,
            target_language=orm_invoice.target_language,
            remarks=orm_invoice.remarks,
            username=orm_invoice.username,
            payment_status=PaymentStatus(orm_invoice.payment_status),
            delivery_status=DeliveryStatus(orm_invoice.delivery_status),
            total_official_docs_count=orm_invoice.total_official_docs_count,
            total_unofficial_docs_count=orm_invoice.total_unofficial_docs_count,
            total_pages_count=orm_invoice.total_pages_count,
            total_judiciary_count=orm_invoice.total_judiciary_count,
            total_foreign_affairs_count=orm_invoice.total_foreign_affairs_count,
            total_additional_doc_count=orm_invoice.total_additional_doc_count,
            items=items
        )

    def _item_orm_to_domain(self, orm_item: InvoiceItemORM) -> InvoiceItem:
        """Convert ORM item model to domain model."""
        return InvoiceItem(
            id=orm_item.id,
            invoice_number=orm_item.invoice_number,
            item_name=orm_item.item_name,
            item_qty=orm_item.item_qty,
            item_price=orm_item.item_price,
            officiality=orm_item.officiality,
            judiciary_seal=orm_item.judiciary_seal,
            foreign_affairs_seal=orm_item.foreign_affairs_seal,
            remarks=orm_item.remarks
        )

    def _domain_to_orm(self, invoice: Invoice) -> InvoiceORM:
        """Convert domain model to ORM model."""
        orm_invoice = InvoiceORM(
            id=invoice.id,
            invoice_number=invoice.invoice_number,
            name=invoice.name,
            national_id=invoice.national_id,
            phone=invoice.phone,
            issue_date=invoice.issue_date,
            delivery_date=invoice.delivery_date,
            translator=invoice.translator,
            total_amount=invoice.total_amount,
            total_translation_price=invoice.total_translation_price,
            advance_payment=invoice.advance_payment,
            discount_amount=invoice.discount_amount,
            force_majeure=invoice.force_majeure,
            final_amount=invoice.final_amount,
            source_language=invoice.source_language,
            target_language=invoice.target_language,
            remarks=invoice.remarks,
            username=invoice.username,
            payment_status=invoice.payment_status.value,
            delivery_status=invoice.delivery_status.value,
            total_official_docs_count=invoice.total_official_docs_count,
            total_unofficial_docs_count=invoice.total_unofficial_docs_count,
            total_pages_count=invoice.total_pages_count,
            total_judiciary_count=invoice.total_judiciary_count,
            total_foreign_affairs_count=invoice.total_foreign_affairs_count,
            total_additional_doc_count=invoice.total_additional_doc_count
        )

        # Convert items
        orm_invoice.items = [self._item_domain_to_orm(item) for item in invoice.items]
        return orm_invoice

    def _item_domain_to_orm(self, item: InvoiceItem) -> InvoiceItemORM:
        """Convert domain item model to ORM model."""
        return InvoiceItemORM(
            id=item.id,
            invoice_number=item.invoice_number,
            item_name=item.item_name,
            item_qty=item.item_qty,
            item_price=item.item_price,
            officiality=item.officiality,
            judiciary_seal=item.judiciary_seal,
            foreign_affairs_seal=item.foreign_affairs_seal,
            remarks=item.remarks
        )

    def get_all(self) -> List[Invoice]:
        with self.db_manager.get_invoices_session() as session:
            orm_invoices = session.query(InvoiceORM).all()
            return [self._orm_to_domain(i) for i in orm_invoices]

    def get_by_number(self, invoice_number: int) -> Optional[Invoice]:
        with self.db_manager.get_invoices_session() as session:
            orm_invoice = session.query(InvoiceORM).filter(InvoiceORM.invoice_number == invoice_number).first()
            return self._orm_to_domain(orm_invoice) if orm_invoice else None

    def get_next_invoice_number(self) -> int:
        with self.db_manager.get_invoices_session() as session:
            last_invoice = session.query(InvoiceORM).order_by(InvoiceORM.invoice_number.desc()).first()
            return last_invoice.invoice_number + 1 if last_invoice else 1000

    def save(self, invoice: Invoice) -> Invoice:
        with self.db_manager.get_invoices_session() as session:
            if invoice.id:
                # Update existing
                orm_invoice = session.query(InvoiceORM).filter(InvoiceORM.id == invoice.id).first()
                if orm_invoice:
                    # Update invoice fields
                    orm_invoice.name = invoice.name
                    orm_invoice.national_id = invoice.national_id
                    orm_invoice.phone = invoice.phone
                    orm_invoice.issue_date = invoice.issue_date
                    orm_invoice.delivery_date = invoice.delivery_date
                    orm_invoice.translator = invoice.translator
                    orm_invoice.total_amount = invoice.total_amount
                    orm_invoice.total_translation_price = invoice.total_translation_price
                    orm_invoice.advance_payment = invoice.advance_payment
                    orm_invoice.discount_amount = invoice.discount_amount
                    orm_invoice.force_majeure = invoice.force_majeure
                    orm_invoice.final_amount = invoice.final_amount
                    orm_invoice.source_language = invoice.source_language
                    orm_invoice.target_language = invoice.target_language
                    orm_invoice.remarks = invoice.remarks
                    orm_invoice.username = invoice.username
                    orm_invoice.payment_status = invoice.payment_status.value
                    orm_invoice.delivery_status = invoice.delivery_status.value
                    orm_invoice.total_official_docs_count = invoice.total_official_docs_count
                    orm_invoice.total_unofficial_docs_count = invoice.total_unofficial_docs_count
                    orm_invoice.total_pages_count = invoice.total_pages_count
                    orm_invoice.total_judiciary_count = invoice.total_judiciary_count
                    orm_invoice.total_foreign_affairs_count = invoice.total_foreign_affairs_count
                    orm_invoice.total_additional_doc_count = invoice.total_additional_doc_count

                    # Update items (cascade will handle deletion)
                    orm_invoice.items = [self._item_domain_to_orm(item) for item in invoice.items]
                else:
                    raise ValueError("Invoice not found")
            else:
                # Create new
                orm_invoice = self._domain_to_orm(invoice)
                session.add(orm_invoice)

            session.flush()  # To get the ID
            return self._orm_to_domain(orm_invoice)

    def delete(self, invoice_id: int) -> bool:
        with self.db_manager.get_invoices_session() as session:
            orm_invoice = session.query(InvoiceORM).filter(InvoiceORM.id == invoice_id).first()
            if orm_invoice:
                session.delete(orm_invoice)
                return True
            return False

    def search(self, criteria: InvoiceSearchCriteria) -> List[Invoice]:
        with self.db_manager.get_invoices_session() as session:
            query = session.query(InvoiceORM)

            if criteria.invoice_number:
                query = query.filter(InvoiceORM.invoice_number == criteria.invoice_number)
            if criteria.customer_name:
                query = query.filter(InvoiceORM.name.ilike(f"%{criteria.customer_name}%"))
            if criteria.national_id:
                query = query.filter(InvoiceORM.national_id == criteria.national_id)
            if criteria.payment_status is not None:
                query = query.filter(InvoiceORM.payment_status == criteria.payment_status.value)
            if criteria.delivery_status is not None:
                query = query.filter(InvoiceORM.delivery_status == criteria.delivery_status.value)
            if criteria.date_from:
                query = query.filter(InvoiceORM.issue_date >= criteria.date_from)
            if criteria.date_to:
                query = query.filter(InvoiceORM.issue_date <= criteria.date_to)

            orm_invoices = query.all()
            return [self._orm_to_domain(i) for i in orm_invoices]

    def get_unpaid_invoices(self) -> List[Invoice]:
        with self.db_manager.get_invoices_session() as session:
            orm_invoices = session.query(InvoiceORM).filter(
                InvoiceORM.payment_status == PaymentStatus.UNPAID.value).all()
            return [self._orm_to_domain(i) for i in orm_invoices]

    def get_pending_delivery_invoices(self) -> List[Invoice]:
        with self.db_manager.get_invoices_session() as session:
            pending_statuses = [
                DeliveryStatus.PENDING.value,
                DeliveryStatus.IN_PROGRESS.value,
                DeliveryStatus.READY.value,
                DeliveryStatus.QUALITY_CHECK.value
            ]
            orm_invoices = session.query(InvoiceORM).filter(InvoiceORM.delivery_status.in_(pending_statuses)).all()
            return [self._orm_to_domain(i) for i in orm_invoices]


# Additional repository classes that might be needed
class SQLAlchemyFixedPriceRepository:
    """SQLAlchemy implementation of fixed price repository."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def _orm_to_domain(self, orm_fixed_price: FixedPriceORM) -> FixedPrice:
        """Convert ORM model to domain model."""
        return FixedPrice(
            id=orm_fixed_price.id,
            name=orm_fixed_price.name,
            price=orm_fixed_price.price
        )

    def get_all(self) -> List[FixedPrice]:
        with self.db_manager.get_services_session() as session:
            orm_fixed_prices = session.query(FixedPriceORM).all()
            return [self._orm_to_domain(fp) for fp in orm_fixed_prices]

    def get_by_name(self, name: str) -> Optional[FixedPrice]:
        with self.db_manager.get_services_session() as session:
            orm_fixed_price = session.query(FixedPriceORM).filter(FixedPriceORM.name == name).first()
            return self._orm_to_domain(orm_fixed_price) if orm_fixed_price else None

    def save(self, fixed_price: FixedPrice) -> FixedPrice:
        with self.db_manager.get_services_session() as session:
            if fixed_price.id:
                # Update existing
                orm_fixed_price = session.query(FixedPriceORM).filter(FixedPriceORM.id == fixed_price.id).first()
                if orm_fixed_price:
                    orm_fixed_price.name = fixed_price.name
                    orm_fixed_price.price = fixed_price.price
                else:
                    raise ValueError("Fixed price not found")
            else:
                # Create new
                orm_fixed_price = FixedPriceORM(
                    name=fixed_price.name,
                    price=fixed_price.price
                )
                session.add(orm_fixed_price)

            session.flush()
            return self._orm_to_domain(orm_fixed_price)


class SQLAlchemyOtherServiceRepository:
    """SQLAlchemy implementation of other service repository."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def _orm_to_domain(self, orm_other_service: OtherServiceORM) -> OtherService:
        """Convert ORM model to domain model."""
        return OtherService(
            id=orm_other_service.id,
            name=orm_other_service.name,
            description=orm_other_service.description
        )

    def get_all(self) -> List[OtherService]:
        with self.db_manager.get_services_session() as session:
            orm_other_services = session.query(OtherServiceORM).all()
            return [self._orm_to_domain(os) for os in orm_other_services]

    def get_by_name(self, name: str) -> Optional[OtherService]:
        with self.db_manager.get_services_session() as session:
            orm_other_service = session.query(OtherServiceORM).filter(OtherServiceORM.name == name).first()
            return self._orm_to_domain(orm_other_service) if orm_other_service else None

    def save(self, other_service: OtherService) -> OtherService:
        with self.db_manager.get_services_session() as session:
            if other_service.id:
                # Update existing
                orm_other_service = session.query(OtherServiceORM).filter(
                    OtherServiceORM.id == other_service.id).first()
                if orm_other_service:
                    orm_other_service.name = other_service.name
                    orm_other_service.description = other_service.description
                else:
                    raise ValueError("Other service not found")
            else:
                # Create new
                orm_other_service = OtherServiceORM(
                    name=other_service.name,
                    description=other_service.description
                )
                session.add(orm_other_service)

            session.flush()
            return self._orm_to_domain(orm_other_service)
