# shared/orm_models/invoices_models.py

from sqlalchemy import Integer, Text, DateTime, ForeignKey, CheckConstraint, Index, event
from sqlalchemy.orm import Mapped, mapped_column, declarative_base, relationship
from typing import Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass

BaseInvoices = declarative_base()


@dataclass
class InvoiceData:
    id: int
    invoice_number: str
    name: str
    national_id: str
    phone: str
    issue_date: datetime
    delivery_date: datetime
    collection_date: Optional[datetime]
    payment_date: Optional[datetime]
    translator: str
    total_items: int
    total_amount: int
    total_translation_price: int
    total_certified_copy_price: int
    total_registration_price: int
    total_confirmation_price: int
    total_additional_issues_price: int
    advance_payment: int
    discount_amount: int
    emergency_cost: int
    final_amount: int
    payment_status: int
    delivery_status: int
    source_language: str
    target_language: str
    username: Optional[str]
    pdf_file_path: Optional[str]
    remarks: Optional[str]


@dataclass
class DeletedInvoiceData:
    id: int
    invoice_number: str
    name: str
    national_id: str
    phone: str
    issue_date: datetime
    delivery_date: datetime
    collection_date: Optional[datetime]
    payment_date: Optional[datetime]
    translator: str
    total_items: int
    total_amount: int
    total_translation_price: int
    total_certified_copy_price: int
    total_registration_price: int
    total_confirmation_price: int
    total_additional_issues_price: int
    final_amount: int
    username: Optional[str]
    remarks: Optional[str]
    deleted_at: datetime
    deleted_by: Optional[str]


@dataclass
class InvoiceItemData:
    id: int
    invoice_number: str
    service_id: int
    service_name: str
    quantity: int
    page_count: int
    additional_issues: int
    is_official: int
    has_judiciary_seal: int
    has_foreign_affairs_seal: int
    dynamic_price_1: int
    dynamic_price_2: int
    dynamic_price_amount_1: int
    dynamic_price_amount_2: int
    remarks: Optional[str]
    translation_price: int
    certified_copy_price: int
    registration_price: int
    judiciary_seal_price: int
    foreign_affairs_seal_price: int
    additional_issues_price: int
    total_price: int


@dataclass
class EditedInvoiceData:
    id: int
    invoice_number: str
    edited_field: str
    old_value: Optional[str]
    new_value: Optional[str]
    edited_by: str
    edited_at: datetime
    remarks: Optional[str]


@dataclass
class WorkspaceBatchData:
    id: int
    batch_number: str
    office_type: str
    created_at: datetime
    sent_by: str
    received_at: Optional[datetime]
    status: str
    remarks: Optional[str]


@dataclass
class WorkspaceBatchItemData:
    id: int
    batch_id: int
    invoice_item_id: int
    sent_at: datetime
    approved_at: Optional[datetime]
    approval_status: str
    remarks: Optional[str]


@dataclass
class WorkspaceQuotaData:
    id: int
    office_type: str
    max_daily: int
    max_weekly: int
    updated_at: datetime

# ---------------------------------------------------------------------
# 🧱 ORM MODELS
# ---------------------------------------------------------------------
class IssuedInvoiceModel(BaseInvoices):
    __tablename__ = 'issued_invoices'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_number: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    name: Mapped[str] = mapped_column(Text, nullable=False)
    national_id: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[str] = mapped_column(Text, nullable=False)

    issue_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    delivery_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    collection_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    payment_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    translator: Mapped[str] = mapped_column(Text, nullable=False)
    total_items: Mapped[int] = mapped_column(Integer, nullable=False)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)

    # --- Price breakdown fields ---
    total_translation_price: Mapped[int] = mapped_column(Integer, default=0)
    total_certified_copy_price: Mapped[int] = mapped_column(Integer, default=0)
    total_registration_price: Mapped[int] = mapped_column(Integer, default=0)
    total_confirmation_price: Mapped[int] = mapped_column(Integer, default=0)
    total_additional_issues_price: Mapped[int] = mapped_column(Integer, default=0)

    advance_payment: Mapped[int] = mapped_column(Integer, default=0)
    discount_amount: Mapped[int] = mapped_column(Integer, default=0)
    emergency_cost: Mapped[int] = mapped_column(Integer, default=0)
    final_amount: Mapped[int] = mapped_column(Integer, nullable=False)

    payment_status: Mapped[int] = mapped_column(Integer, default=0)
    delivery_status: Mapped[int] = mapped_column(Integer, default=0)

    source_language: Mapped[str] = mapped_column(Text, nullable=False)
    target_language: Mapped[str] = mapped_column(Text, nullable=False)

    username: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pdf_file_path: Mapped[Optional[str]] = mapped_column(Text)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    items: Mapped[List["InvoiceItemModel"]] = relationship(
        "InvoiceItemModel",
        cascade="all, delete-orphan",
        back_populates="invoice"
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

    def to_dataclass(self) -> InvoiceData:
        return InvoiceData(
            id=self.id,
            invoice_number=self.invoice_number,
            name=self.name,
            national_id=self.national_id,
            phone=self.phone,
            issue_date=self.issue_date,
            delivery_date=self.delivery_date,
            collection_date=self.collection_date,
            payment_date=self.payment_date,
            translator=self.translator,
            total_items=self.total_items,
            total_amount=self.total_amount,
            total_translation_price=self.total_translation_price,
            total_certified_copy_price=self.total_certified_copy_price,
            total_registration_price=self.total_registration_price,
            total_confirmation_price=self.total_confirmation_price,
            total_additional_issues_price=self.total_additional_issues_price,
            advance_payment=self.advance_payment,
            discount_amount=self.discount_amount,
            emergency_cost=self.emergency_cost,
            final_amount=self.final_amount,
            payment_status=self.payment_status,
            delivery_status=self.delivery_status,
            source_language=self.source_language,
            target_language=self.target_language,
            username=self.username,
            pdf_file_path=self.pdf_file_path,
            remarks=self.remarks,
        )


@event.listens_for(IssuedInvoiceModel, 'before_update', propagate=True)
def before_update_listener(mapper, connection, target):
    if target.delivery_status == 4 and target.collection_date is None:
        target.collection_date = datetime.now(timezone.utc)
    if target.payment_status == 1 and target.payment_date is None:
        target.payment_date = datetime.now(timezone.utc)


class DeletedInvoiceModel(BaseInvoices):
    """A table to store invoices that have been deleted."""
    __tablename__ = 'deleted_invoices'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_number: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    national_id: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[str] = mapped_column(Text, nullable=False)
    issue_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    delivery_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    collection_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    payment_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    translator: Mapped[str] = mapped_column(Text, nullable=False)
    total_items: Mapped[int] = mapped_column(Integer, nullable=False)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)

    # --- Price breakdown fields ---
    total_translation_price: Mapped[int] = mapped_column(Integer, default=0)
    total_certified_copy_price: Mapped[int] = mapped_column(Integer, default=0)
    total_registration_price: Mapped[int] = mapped_column(Integer, default=0)
    total_confirmation_price: Mapped[int] = mapped_column(Integer, default=0)
    total_additional_issues_price: Mapped[int] = mapped_column(Integer, default=0)

    advance_payment: Mapped[int] = mapped_column(Integer, default=0)
    discount_amount: Mapped[int] = mapped_column(Integer, default=0)
    emergency_cost: Mapped[int] = mapped_column(Integer, default=0)
    final_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_status: Mapped[int] = mapped_column(Integer, default=0)
    delivery_status: Mapped[int] = mapped_column(Integer, default=0)
    source_language: Mapped[str] = mapped_column(Text, nullable=False)
    target_language: Mapped[str] = mapped_column(Text, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pdf_file_path: Mapped[Optional[str]] = mapped_column(Text)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    deleted_by: Mapped[str] = mapped_column(Text, nullable=True)

    def to_dataclass(self) -> DeletedInvoiceData:
        return DeletedInvoiceData(
            id=self.id,
            invoice_number=self.invoice_number,
            name=self.name,
            national_id=self.national_id,
            phone=self.phone,
            issue_date=self.issue_date,
            delivery_date=self.delivery_date,
            collection_date=self.collection_date,
            payment_date=self.payment_date,
            translator=self.translator,
            total_items=self.total_items,
            total_amount=self.total_amount,
            total_translation_price=self.total_translation_price,
            total_certified_copy_price=self.total_certified_copy_price,
            total_registration_price=self.total_registration_price,
            total_confirmation_price=self.total_confirmation_price,
            total_additional_issues_price=self.total_additional_issues_price,
            final_amount=self.final_amount,
            username=self.username,
            remarks=self.remarks,
            deleted_at=self.deleted_at,
            deleted_by=self.deleted_by
        )


class EditedInvoiceModel(BaseInvoices):
    """
    Tracks any edits made to issued invoices, such as delivery date changes or item modifications.
    Each record represents a single field-level change.
    """
    __tablename__ = "edited_invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    invoice_number: Mapped[str] = mapped_column(
        Text,
        ForeignKey("issued_invoices.invoice_number", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    edited_field: Mapped[str] = mapped_column(Text, nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    edited_by: Mapped[str] = mapped_column(Text, nullable=False)
    edited_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index('idx_edited_invoices_invoice_number', 'invoice_number'),
        Index('idx_edited_invoices_edited_by', 'edited_by'),
        Index('idx_edited_invoices_edited_at', 'edited_at'),
    )

    def to_dataclass(self) -> EditedInvoiceData:
        """
        Converts the ORM model into a simple dataclass for easy transport between layers.
        """
        return EditedInvoiceData(
            id=self.id,
            invoice_number=self.invoice_number,
            edited_field=self.edited_field,
            old_value=self.old_value,
            new_value=self.new_value,
            edited_by=self.edited_by,
            edited_at=self.edited_at,
            remarks=self.remarks,
        )


class InvoiceItemModel(BaseInvoices):
    __tablename__ = 'invoice_items'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_number: Mapped[str] = mapped_column(
        Text,
        ForeignKey("issued_invoices.invoice_number", ondelete="CASCADE"),
        nullable=False
    )

    service_id: Mapped[int] = mapped_column(Integer, nullable=False)
    service_name: Mapped[str] = mapped_column(Text, nullable=False)
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

    invoice: Mapped["IssuedInvoiceModel"] = relationship(back_populates="items")

    __table_args__ = (
        CheckConstraint('is_official IN (0, 1)', name='check_is_official'),
        CheckConstraint('has_judiciary_seal IN (0, 1)', name='check_has_judiciary_seal'),
        CheckConstraint('has_foreign_affairs_seal IN (0, 1)', name='check_has_foreign_affairs_seal'),
        Index('idx_invoice_items_invoice_number', 'invoice_number'),
        Index('idx_invoice_items_official', 'is_official'),
        Index('idx_invoice_items_judiciary', 'has_judiciary_seal'),
        Index('idx_invoice_items_foreign', 'has_foreign_affairs_seal'),
    )

    def to_dataclass(self) -> InvoiceItemData:
        return InvoiceItemData(
            id=self.id,
            invoice_number=self.invoice_number,
            service_id=self.service_id,
            service_name=self.service_name,
            quantity=self.quantity,
            page_count=self.page_count,
            additional_issues=self.additional_issues,
            is_official=self.is_official,
            has_judiciary_seal=self.has_judiciary_seal,
            has_foreign_affairs_seal=self.has_foreign_affairs_seal,
            dynamic_price_1=self.dynamic_price_1,
            dynamic_price_2=self.dynamic_price_2,
            dynamic_price_amount_1=self.dynamic_price_amount_1,
            dynamic_price_amount_2=self.dynamic_price_amount_2,
            remarks=self.remarks,
            translation_price=self.translation_price,
            certified_copy_price=self.certified_copy_price,
            registration_price=self.registration_price,
            judiciary_seal_price=self.judiciary_seal_price,
            foreign_affairs_seal_price=self.foreign_affairs_seal_price,
            additional_issues_price=self.additional_issues_price,
            total_price=self.total_price,
        )


class WorkspaceBatchModel(BaseInvoices):
    """
    Represents a batch of documents sent to an external office (e.g., judiciary or foreign affairs).
    """
    __tablename__ = "workspace_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_number: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    office_type: Mapped[str] = mapped_column(Text, nullable=False)  # 'judiciary' | 'foreign_affairs'
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    sent_by: Mapped[str] = mapped_column(Text, nullable=False)
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(Text, default="pending")  # 'pending', 'sent', 'approved', 'returned', 'rejected'
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    items: Mapped[List["WorkspaceBatchItemModel"]] = relationship(
        "WorkspaceBatchItemModel",
        cascade="all, delete-orphan",
        back_populates="batch"
    )

    __table_args__ = (
        Index('idx_workspace_batches_office_type', 'office_type'),
        Index('idx_workspace_batches_status', 'status'),
        Index('idx_workspace_batches_created_at', 'created_at'),
    )

    def to_dataclass(self) -> WorkspaceBatchData:
        return WorkspaceBatchData(
            id=self.id,
            batch_number=self.batch_number,
            office_type=self.office_type,
            created_at=self.created_at,
            sent_by=self.sent_by,
            received_at=self.received_at,
            status=self.status,
            remarks=self.remarks
        )


class WorkspaceBatchItemModel(BaseInvoices):
    """
    Links individual invoice items to workspace batches.
    Tracks when each item was sent, approved, or rejected.
    """
    __tablename__ = "workspace_batch_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("workspace_batches.id", ondelete="CASCADE"), nullable=False)
    invoice_item_id: Mapped[int] = mapped_column(ForeignKey("invoice_items.id", ondelete="CASCADE"), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approval_status: Mapped[str] = mapped_column(Text, default="pending")  # 'pending', 'approved', 'rejected'
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    batch: Mapped["WorkspaceBatchModel"] = relationship(back_populates="items")
    invoice_item: Mapped["InvoiceItemModel"] = relationship()  # Read-only link to item details

    __table_args__ = (
        Index('idx_workspace_batch_items_batch_id', 'batch_id'),
        Index('idx_workspace_batch_items_status', 'approval_status'),
        Index('idx_workspace_batch_items_invoice_item', 'invoice_item_id'),
    )

    def to_dataclass(self) -> WorkspaceBatchItemData:
        return WorkspaceBatchItemData(
            id=self.id,
            batch_id=self.batch_id,
            invoice_item_id=self.invoice_item_id,
            sent_at=self.sent_at,
            approved_at=self.approved_at,
            approval_status=self.approval_status,
            remarks=self.remarks
        )


class WorkspaceQuotaModel(BaseInvoices):
    """
    Defines quotas for how many documents can be sent to each office (daily/weekly limits).
    """
    __tablename__ = "workspace_quotas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    office_type: Mapped[str] = mapped_column(Text, nullable=False, unique=True)  # judiciary | foreign_affairs
    max_daily: Mapped[int] = mapped_column(Integer, default=0)
    max_weekly: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc),
                                                 onupdate=datetime.now(timezone.utc))

    __table_args__ = (
        Index('idx_workspace_quotas_office_type', 'office_type'),
    )

    def to_dataclass(self) -> WorkspaceQuotaData:
        return WorkspaceQuotaData(
            id=self.id,
            office_type=self.office_type,
            max_daily=self.max_daily,
            max_weekly=self.max_weekly,
            updated_at=self.updated_at
        )
