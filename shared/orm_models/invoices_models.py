# shared/orm_models/invoices_models

from sqlalchemy import (
    Integer, Text, Date, ForeignKey, CheckConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, declarative_base
from typing import Optional
from datetime import date


BaseInvoices = declarative_base()


class IssuedInvoiceModel(BaseInvoices):
    __tablename__ = 'issued_invoices'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_number: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    name: Mapped[str] = mapped_column(Text, nullable=False)
    national_id: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[str] = mapped_column(Text, nullable=False)

    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    delivery_date: Mapped[date] = mapped_column(Date, nullable=False)

    translator: Mapped[str] = mapped_column(Text, nullable=False)

    total_items: Mapped[int] = mapped_column(Integer, nullable=False)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    total_translation_price: Mapped[int] = mapped_column(Integer, nullable=False)
    advance_payment: Mapped[int] = mapped_column(Integer, default=0)
    discount_amount: Mapped[int] = mapped_column(Integer, default=0)

    emergency_cost: Mapped[int] = mapped_column( Integer, default=0)

    final_amount: Mapped[int] = mapped_column(Integer, nullable=False)

    payment_status: Mapped[int] = mapped_column(Integer, default=0)
    delivery_status: Mapped[int] = mapped_column(Integer, default=0)

    source_language: Mapped[str] = mapped_column(Text, nullable=False)
    target_language: Mapped[str] = mapped_column(Text, nullable=False)

    username: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pdf_file_path: Mapped[Optional[str]] = mapped_column(Text)

    # --- NEW: Added remarks field to match DTOs ---
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint('payment_status IN (0, 1)', name='check_payment_status'),
        CheckConstraint('delivery_status IN (0, 1, 2, 3, 4)', name='check_delivery_status'),
        Index('idx_issued_invoices_delivery_date', 'delivery_date'),
        Index('idx_issued_invoices_delivery_status', 'delivery_status'),
        Index('idx_issued_invoices_invoice_status', 'payment_status'),
        Index('idx_issued_invoices_issue_date', 'issue_date'),
        Index('idx_issued_invoices_national_id', 'national_id'),
        Index('idx_issued_invoices_translator', 'translator'),
        Index('idx_issued_invoices_user', 'username'),
    )


class InvoiceItemModel(BaseInvoices):
    __tablename__ = 'invoice_items'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_number: Mapped[str] = mapped_column(
        Text,
        ForeignKey("issued_invoices.invoice_number", ondelete="CASCADE"),
        nullable=False
    )

    service: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    additional_issues: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_official: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    has_judiciary_seal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    has_foreign_affairs_seal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dynamic_price_1: Mapped[int] = mapped_column(Integer, default=0)
    dynamic_price_2: Mapped[int] = mapped_column(Integer, default=0)
    dynamic_price_amount_1: Mapped[int] = mapped_column(Integer, default=0)
    dynamic_price_amount_2: Mapped[int] = mapped_column(Integer, default=0)
    remarks: Mapped[Optional[str]] = mapped_column(Text)
    translation_price: Mapped[int] = mapped_column(Integer, default=0)
    certified_copy_price: Mapped[int] = mapped_column(Integer, default=0)
    registration_price: Mapped[int] = mapped_column(Integer, default=0)
    judiciary_seal_price: Mapped[int] = mapped_column(Integer, default=0)
    foreign_affairs_seal_price: Mapped[int] = mapped_column(Integer, default=0)
    additional_issues_price: Mapped[int] = mapped_column(Integer, default=0)
    total_price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        CheckConstraint('is_official IN (0, 1)', name='check_is_official'),
        CheckConstraint('has_judiciary_seal IN (0, 1)', name='check_has_judiciary_seal'),
        CheckConstraint('has_foreign_affairs_seal IN (0, 1)', name='check_has_foreign_affairs_seal'),
        Index('idx_invoice_items_invoice_number', 'invoice_number'),
        Index('idx_invoice_items_official', 'is_official'),
        Index('idx_invoice_items_judiciary', 'has_judiciary_seal'),
        Index('idx_invoice_items_foreign', 'has_foreign_affairs_seal'),
    )
