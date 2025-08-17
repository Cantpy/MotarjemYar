from sqlalchemy import (
    Integer, Text, Date, ForeignKey, CheckConstraint, Index, VARCHAR, Boolean
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base
from typing import Optional


BaseInvoices = declarative_base()


class IssuedInvoiceModel(BaseInvoices):
    __tablename__ = 'issued_invoices'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    national_id: Mapped[int] = mapped_column(Integer, nullable=False)
    phone: Mapped[str] = mapped_column(Text, nullable=False)
    issue_date: Mapped[Date] = mapped_column(Date, nullable=False)
    delivery_date: Mapped[Date] = mapped_column(Date, nullable=False)
    translator: Mapped[str] = mapped_column(Text, nullable=False)
    total_items: Mapped[Optional[int]] = mapped_column(Integer)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    total_translation_price: Mapped[int] = mapped_column(Integer, nullable=False)
    advance_payment: Mapped[int] = mapped_column(Integer, default=0)
    discount_amount: Mapped[int] = mapped_column(Integer, default=0)
    force_majeure: Mapped[int] = mapped_column(Integer, default=0)
    final_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_status: Mapped[int] = mapped_column(Integer, default=0)
    delivery_status: Mapped[int] = mapped_column(Integer, default=0)
    total_official_docs_count: Mapped[int] = mapped_column(Integer, default=0)
    total_unofficial_docs_count: Mapped[int] = mapped_column(Integer, default=0)
    total_pages_count: Mapped[int] = mapped_column(Integer, default=0)
    total_judiciary_count: Mapped[int] = mapped_column(Integer, default=0)
    total_foreign_affairs_count: Mapped[int] = mapped_column(Integer, default=0)
    total_additional_doc_count: Mapped[int] = mapped_column(Integer, default=0)
    source_language: Mapped[Optional[str]] = mapped_column(Text)
    target_language: Mapped[Optional[str]] = mapped_column(Text)
    username: Mapped[Optional[str]] = mapped_column(
        Text, ForeignKey("users.username", ondelete="SET NULL")
    )
    pdf_file_path: Mapped[Optional[str]] = mapped_column(Text)

    # One-to-many: IssuedInvoice → InvoiceItems
    invoice_items: Mapped[list["InvoiceItemModel"]] = relationship(
        "InvoiceItemModel",
        back_populates="issued_invoice",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

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
    invoice_number: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("issued_invoices.invoice_number", ondelete="CASCADE"),
        nullable=False
    )
    item_name: Mapped[str] = mapped_column(Text, nullable=False)
    item_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    item_price: Mapped[int] = mapped_column(Integer, nullable=False)
    officiality: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    judiciary_seal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    foreign_affairs_seal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Many-to-one: InvoiceItem → IssuedInvoice
    issued_invoice: Mapped["IssuedInvoiceModel"] = relationship(
        "IssuedInvoiceModel", back_populates="invoice_items"
    )

    __table_args__ = (
        CheckConstraint('officiality IN (0, 1)', name='check_officiality'),
        CheckConstraint('judiciary_seal IN (0, 1)', name='check_judiciary_seal'),
        CheckConstraint('foreign_affairs_seal IN (0, 1)', name='check_foreign_affairs_seal'),
        Index('idx_invoice_items_foreign', 'foreign_affairs_seal'),
        Index('idx_invoice_items_invoice_id', 'invoice_number'),
        Index('idx_invoice_items_judiciary', 'judiciary_seal'),
        Index('idx_invoice_items_official', 'officiality'),
    )
