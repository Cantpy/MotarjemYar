# -*- coding: utf-8 -*-

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint, Boolean, \
    Date, Text, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()


class Customer(Base):
    __tablename__ = 'customers'

    national_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False, unique=True)
    telegram_id = Column(String)
    email = Column(String)
    address = Column(String)
    passport_image = Column(String)

    # Relationships
    invoices = relationship("IssuedInvoice", back_populates="customer")

    def __repr__(self):
        return f"<Customer(national_id='{self.national_id}', name='{self.name}')>"


class Service(Base):
    __tablename__ = 'Services'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    base_price = Column(Integer)
    dynamic_price_name_1 = Column(Text)
    dynamic_price_1 = Column(Integer)
    dynamic_price_name_2 = Column(Text)
    dynamic_price_2 = Column(Integer)

    def __repr__(self):
        return f"<Service(name='{self.name}', base_price={self.base_price})>"


class FixedPrice(Base):
    __tablename__ = 'fixed_prices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True)
    price = Column(Integer, nullable=False, default=0)
    is_default = Column(Boolean, nullable=False, default=False)
    label_name = Column(Text)

    def __repr__(self):
        return f"<FixedPrice(name='{self.name}', price={self.price})>"


class OtherService(Base):
    __tablename__ = 'other_services'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True)
    price = Column(Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<OtherService(name='{self.name}', price={self.price})>"


class IssuedInvoice(Base):
    __tablename__ = 'issued_invoices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(Integer, nullable=False, unique=True)
    name = Column(String, nullable=False)
    national_id = Column(String, ForeignKey('customers.national_id'), nullable=False)
    phone = Column(String, nullable=False)
    issue_date = Column(Date, nullable=False)
    delivery_date = Column(Date, nullable=False)
    translator = Column(String, nullable=False)
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
    source_language = Column(String)
    target_language = Column(String)
    remarks = Column(Text)
    username = Column(String)
    pdf_file_path = Column(String)

    # Constraints
    __table_args__ = (
        CheckConstraint('payment_status IN (0, 1)', name='check_payment_status'),
        CheckConstraint('delivery_status IN (0, 1, 2, 3, 4)', name='check_delivery_status'),
    )

    # Relationships
    customer = relationship("Customer", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<IssuedInvoice(invoice_number={self.invoice_number}, total_amount={self.total_amount})>"


class InvoiceItem(Base):
    __tablename__ = 'invoice_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(Integer, ForeignKey('issued_invoices.invoice_number', ondelete='CASCADE'), nullable=False)
    item_name = Column(String, nullable=False)
    item_qty = Column(Integer, nullable=False, default=1)
    item_price = Column(Integer, nullable=False)
    officiality = Column(Integer, nullable=False, default=0)
    judiciary_seal = Column(Integer, nullable=False, default=0)
    foreign_affairs_seal = Column(Integer, nullable=False, default=0)
    remarks = Column(Text)

    # Constraints
    __table_args__ = (
        CheckConstraint('officiality IN (0, 1)', name='check_officiality'),
        CheckConstraint('judiciary_seal IN (0, 1)', name='check_judiciary_seal'),
        CheckConstraint('foreign_affairs_seal IN (0, 1)', name='check_foreign_affairs_seal'),
    )

    # Relationships
    invoice = relationship("IssuedInvoice", back_populates="items")

    def __repr__(self):
        return f"<InvoiceItem(item_name='{self.item_name}', item_qty={self.item_qty}, item_price={self.item_price})>"


class DatabaseManager:
    """Manages database connections and sessions for the invoice system."""

    def __init__(self, customers_db_path, invoices_db_path, services_db_path):
        # Create engines for each database
        self.customers_engine = create_engine(f'sqlite:///{customers_db_path}', echo=False)
        self.invoices_engine = create_engine(f'sqlite:///{invoices_db_path}', echo=False)
        self.services_engine = create_engine(f'sqlite:///{services_db_path}', echo=False)

        # Create session makers
        self.CustomersSession = sessionmaker(bind=self.customers_engine)
        self.InvoicesSession = sessionmaker(bind=self.invoices_engine)
        self.ServicesSession = sessionmaker(bind=self.services_engine)

        # Create tables
        self.create_tables()

    def create_tables(self):
        """Create all tables in their respective databases."""
        # Create customers table
        Base.metadata.create_all(self.customers_engine, tables=[Customer.__table__])

        # Create invoices and invoice_items tables
        Base.metadata.create_all(self.invoices_engine, tables=[IssuedInvoice.__table__, InvoiceItem.__table__])

        # Create services, fixed_prices, and other_services tables
        Base.metadata.create_all(self.services_engine,
                                 tables=[Service.__table__, FixedPrice.__table__, OtherService.__table__])

    def get_customers_session(self):
        """Get a new session for customers database."""
        return self.CustomersSession()

    def get_invoices_session(self):
        """Get a new session for invoices database."""
        return self.InvoicesSession()

    def get_services_session(self):
        """Get a new session for services database."""
        return self.ServicesSession()

    def close_all_connections(self):
        """Close all database connections."""
        self.customers_engine.dispose()
        self.invoices_engine.dispose()
        self.services_engine.dispose()


# Utility functions for common operations
def get_customer_by_national_id(session, national_id):
    """Get a customer by their national ID."""
    return session.query(Customer).filter_by(national_id=national_id).first()


def get_invoice_by_number(session, invoice_number):
    """Get an invoice by its invoice number."""
    return session.query(IssuedInvoice).filter_by(invoice_number=invoice_number).first()


def get_service_by_name(session, service_name):
    """Get a service by its name."""
    return session.query(Service).filter_by(name=service_name).first()


def get_fixed_price_by_name(session, price_name):
    """Get a fixed price by its name."""
    return session.query(FixedPrice).filter_by(name=price_name).first()


def get_other_service_by_name(session, service_name):
    """Get an other service by its name."""
    return session.query(OtherService).filter_by(name=service_name).first()


def get_invoice_items_by_invoice_number(session, invoice_number):
    """Get all invoice items for a specific invoice."""
    return session.query(InvoiceItem).filter_by(invoice_number=invoice_number).all()


def get_unpaid_invoices(session):
    """Get all unpaid invoices."""
    return session.query(IssuedInvoice).filter_by(payment_status=0).all()


def get_pending_delivery_invoices(session):
    """Get all invoices with pending delivery status."""
    return session.query(IssuedInvoice).filter(IssuedInvoice.delivery_status.in_([0, 1, 2, 3])).all()


def get_invoices_by_translator(session, translator_name):
    """Get all invoices handled by a specific translator."""
    return session.query(IssuedInvoice).filter_by(translator=translator_name).all()


def get_invoices_by_date_range(session, start_date, end_date):
    """Get invoices within a specific date range."""
    return session.query(IssuedInvoice).filter(
        IssuedInvoice.issue_date >= start_date,
        IssuedInvoice.issue_date <= end_date
    ).all()


def calculate_invoice_totals(session, invoice_number):
    """Calculate various totals for an invoice based on its items."""
    items = get_invoice_items_by_invoice_number(session, invoice_number)

    total_items_price = sum(item.item_qty * item.item_price for item in items)
    total_items = len(items)
    total_official_docs = sum(item.officiality for item in items)
    total_judiciary_docs = sum(item.judiciary_seal for item in items)
    total_foreign_docs = sum(item.foreign_affairs_seal for item in items)

    return {
        'total_items_price': total_items_price,
        'total_items': total_items,
        'total_official_docs': total_official_docs,
        'total_judiciary_docs': total_judiciary_docs,
        'total_foreign_docs': total_foreign_docs
    }
