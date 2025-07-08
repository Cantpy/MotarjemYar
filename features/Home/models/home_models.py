"""
Database models for the home page using SQLAlchemy ORM.
"""

from sqlalchemy import (
    Column, Integer, String, Date, Text, ForeignKey,
    CheckConstraint, Index, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
from datetime import date
import json
from typing import List, Dict, Any, Optional

Base = declarative_base()


class Customer(Base):
    """Customer model for the customers database."""
    __tablename__ = 'customers'

    national_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False, unique=True)
    telegram_id = Column(String)
    email = Column(String)
    address = Column(String)
    passport_image = Column(String)

    # Relationship to invoices
    invoices = relationship("IssuedInvoice", back_populates="customer")

    def __repr__(self):
        return f"<Customer(national_id='{self.national_id}', name='{self.name}')>"


class IssuedInvoice(Base):
    """Invoice model for the invoices database."""
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
        # Indexes
        Index('idx_issued_invoices_delivery_date', 'delivery_date'),
        Index('idx_issued_invoices_delivery_status', 'delivery_status'),
        Index('idx_issued_invoices_invoice_status', 'payment_status'),
        Index('idx_issued_invoices_issue_date', 'issue_date'),
        Index('idx_issued_invoices_national_id', 'national_id'),
        Index('idx_issued_invoices_translator', 'translator'),
        Index('idx_issued_invoices_user', 'username'),
    )

    # Relationships
    customer = relationship("Customer", back_populates="invoices")
    invoice_items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<IssuedInvoice(invoice_number={self.invoice_number}, name='{self.name}')>"

    @property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue based on delivery date."""
        return self.delivery_date < date.today()

    @property
    def days_until_delivery(self) -> int:
        """Calculate days until delivery date."""
        return (self.delivery_date - date.today()).days

    @property
    def is_delivered(self) -> bool:
        """Check if invoice has been delivered."""
        return self.delivery_status == 1


class InvoiceItem(Base):
    """Invoice item model for individual items within invoices."""
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
        # Indexes
        Index('idx_invoice_items_invoice_id', 'invoice_number'),
        Index('idx_invoice_items_official', 'officiality'),
        Index('idx_invoice_items_judiciary', 'judiciary_seal'),
        Index('idx_invoice_items_foreign', 'foreign_affairs_seal'),
    )

    # Relationships
    invoice = relationship("IssuedInvoice", back_populates="invoice_items")

    def __repr__(self):
        return f"<InvoiceItem(id={self.id}, item_name='{self.item_name}', qty={self.item_qty})>"

    @property
    def total_price(self) -> int:
        """Calculate total price for this item."""
        return self.item_qty * self.item_price


class DatabaseManager:
    """Database manager for handling multiple database connections."""

    def __init__(self, customers_db_path: str, invoices_db_path: str):
        self.customers_db_path = customers_db_path
        self.invoices_db_path = invoices_db_path

        # Create engines for each database
        self.customers_engine = create_engine(f'sqlite:///{customers_db_path}')
        self.invoices_engine = create_engine(f'sqlite:///{invoices_db_path}')

        # Create session factories
        self.CustomersSession = sessionmaker(bind=self.customers_engine)
        self.InvoicesSession = sessionmaker(bind=self.invoices_engine)

        # Create tables
        self._create_tables()

    def _create_tables(self):
        """Create all tables in both databases."""
        # Create customers table
        Customer.metadata.create_all(self.customers_engine)

        # Create invoices and invoice_items tables
        IssuedInvoice.metadata.create_all(self.invoices_engine)
        InvoiceItem.metadata.create_all(self.invoices_engine)

    def get_customers_session(self):
        """Get a session for customers database."""
        return self.CustomersSession()

    def get_invoices_session(self):
        """Get a session for invoices database."""
        return self.InvoicesSession()

    def get_dashboard_stats(self) -> Dict[str, int]:
        """Get all dashboard statistics."""
        stats = {}

        # Get customer count
        with self.get_customers_session() as session:
            stats['total_customers'] = session.query(Customer).count()

        # Get invoice statistics
        with self.get_invoices_session() as session:
            # Total invoices
            stats['total_invoices'] = session.query(IssuedInvoice).count()

            # Today's invoices
            today = date.today()
            stats['today_invoices'] = session.query(IssuedInvoice).filter(
                IssuedInvoice.issue_date == today
            ).count()

            # Document counts
            doc_stats = self._get_document_counts(session)
            stats.update(doc_stats)

        return stats

    def _get_document_counts(self, session) -> Dict[str, int]:
        """Calculate document counts from invoice items."""
        total_docs = 0
        available_docs = 0

        # Get all invoice items with their delivery status
        query = session.query(InvoiceItem, IssuedInvoice.delivery_status).join(
            IssuedInvoice, InvoiceItem.invoice_number == IssuedInvoice.invoice_number
        )

        for item, delivery_status in query.all():
            doc_count = item.item_qty
            total_docs += doc_count

            if delivery_status == 0:  # Not delivered
                available_docs += doc_count

        return {
            'total_documents': total_docs,
            'available_documents': available_docs
        }

    def get_recent_invoices(self, limit: int = 20) -> List[IssuedInvoice]:
        """Get recent invoices sorted by delivery date."""
        with self.get_invoices_session() as session:
            return session.query(IssuedInvoice).filter(
                IssuedInvoice.delivery_date != 'نامشخص'
            ).order_by(IssuedInvoice.delivery_date.asc()).limit(limit).all()

    def mark_invoice_delivered(self, invoice_number: int) -> bool:
        """Mark an invoice as delivered."""
        with self.get_invoices_session() as session:
            invoice = session.query(IssuedInvoice).filter_by(
                invoice_number=invoice_number
            ).first()

            if invoice:
                invoice.delivery_status = 1
                session.commit()
                return True
            return False

    def get_invoice_by_number(self, invoice_number: int) -> Optional[IssuedInvoice]:
        """Get invoice by invoice number."""
        with self.get_invoices_session() as session:
            return session.query(IssuedInvoice).filter_by(
                invoice_number=invoice_number
            ).first()

    def get_customer_by_national_id(self, national_id: str) -> Optional[Customer]:
        """Get customer by national ID."""
        with self.get_customers_session() as session:
            return session.query(Customer).filter_by(
                national_id=national_id
            ).first()

    def get_most_frequent_document_type(self) -> str:
        """Get the most frequently translated document type."""
        with self.get_invoices_session() as session:
            # This would need to be implemented based on how document types are stored
            # For now, returning a placeholder
            return "گذرنامه"

    def get_most_frequent_document_this_month(self) -> str:
        """Get the most frequently translated document type this month."""
        with self.get_invoices_session() as session:
            # This would need to be implemented based on how document types are stored
            # For now, returning a placeholder
            return "شناسنامه"

    def close(self):
        """Close all database connections and clean up resources."""
        try:
            # Dispose of the database engines
            if hasattr(self, 'customers_engine') and self.customers_engine:
                self.customers_engine.dispose()

            if hasattr(self, 'invoices_engine') and self.invoices_engine:
                self.invoices_engine.dispose()

        except Exception as e:
            print(f"Error closing database connections: {e}")
            # Log the error if you have a logger
            # logger.error(f"Error closing database connections: {e}")

        finally:
            # Set engines to None to prevent further use
            self.customers_engine = None
            self.invoices_engine = None
            self.CustomersSession = None
            self.InvoicesSession = None
