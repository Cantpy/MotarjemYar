# shared/orm_models/business_models.py

"""
SQLAlchemy ORM models for the Business domain, including Users, Customers,
Services, and Invoices.
Defines the database schema and relationships for the business logic layer.
"""

from __future__ import annotations
from typing import Optional, List
from datetime import datetime, timezone, date
from dataclasses import dataclass

from sqlalchemy import (
    Integer, Text, String, Date, DateTime, LargeBinary,
    ForeignKey, CheckConstraint, Index, event, func
)
from sqlalchemy.orm import relationship, Mapped, mapped_column, declarative_base


# One Base to rule them all
BaseBusiness = declarative_base()


# ---------------------------------------------------------------------
# 📦 DATACLASSES (Data Transfer Objects)
# ---------------------------------------------------------------------

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


@dataclass
class TranslationOfficeData:
    id: int
    license_key: str
    name: str
    reg_no: Optional[str]
    representative: Optional[str]
    manager: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]
    whatsapp: Optional[str]
    instagram: Optional[str]
    telegram: Optional[str]
    other_media: Optional[str]
    open_hours: Optional[str]
    logo: Optional[bytes]
    map_url: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class UsersData:
    id: int
    username: str
    password_hash: bytes
    role: str
    active: int
    display_name: str
    avatar_path: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    token_hash: Optional[str]
    expires_at: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    failed_login_attempts: int
    lockout_until_utc: Optional[datetime]


# ---------------------------------------------------------------------
# 👤 USERS DOMAIN
# ---------------------------------------------------------------------

class UsersModel(BaseBusiness):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_hash: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_path: Mapped[Optional[str]] = mapped_column(Text)
    start_date: Mapped[Optional[str]] = mapped_column(Text)
    end_date: Mapped[Optional[str]] = mapped_column(Text)
    token_hash: Mapped[Optional[str]] = mapped_column(Text)
    expires_at: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[Optional[str]] = mapped_column(Text)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default='0')
    lockout_until_utc: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    edited_logs: Mapped[list["EditedUsersLogModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    deleted_records: Mapped[list["DeletedUsersModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    login_logs: Mapped[list["LoginLogsModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    security_questions: Mapped[list["SecurityQuestionModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    invoices: Mapped[list["IssuedInvoiceModel"]] = relationship(
        "IssuedInvoiceModel", back_populates="user"
    )

    expenses: Mapped[list["ExpenseModel"]] = relationship(
        "ExpenseModel", back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<UsersModel(id={self.id}, username={self.username!r}, role={self.role!r})>"


class EditedUsersLogModel(BaseBusiness):
    __tablename__ = "edited_users_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    editor_username: Mapped[str] = mapped_column(Text, nullable=False)
    field_name: Mapped[str] = mapped_column(Text, nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp(), nullable=False)

    user: Mapped[UsersModel] = relationship("UsersModel", back_populates="edited_logs")

    __table_args__ = (
        Index("idx_edited_users_user_id", "user_id"),
        Index("idx_edited_users_field_name", "field_name"),
        Index("idx_edited_users_changed_at", "changed_at"),
    )


class DeletedUsersModel(BaseBusiness):
    __tablename__ = "deleted_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    original_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    username: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    role: Mapped[Optional[str]] = mapped_column(Text)
    deleted_by: Mapped[str] = mapped_column(Text, nullable=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp(), nullable=False)

    user: Mapped[Optional["UsersModel"]] = relationship("UsersModel", back_populates="deleted_records")

    __table_args__ = (
        Index("idx_deleted_users_original_id", "original_user_id"),
        Index("idx_deleted_users_username", "username"),
        Index("idx_deleted_users_deleted_at", "deleted_at"),
    )


class LoginLogsModel(BaseBusiness):
    __tablename__ = 'login_logs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    login_time: Mapped[str | None] = mapped_column(Text)
    logout_time: Mapped[str | None] = mapped_column(Text)
    time_on_app: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(Text)
    user_agent: Mapped[str | None] = mapped_column(Text)

    user: Mapped[UsersModel] = relationship("UsersModel", back_populates="login_logs")

    __table_args__ = (
        CheckConstraint("status IN ('success', 'failed', 'auto_login_success')", name='check_status'),
        Index('idx_login_logs_user_id', 'user_id'),
        Index('idx_login_logs_status', 'status'),
        Index('idx_login_logs_time', 'login_time'),
    )


class SecurityQuestionModel(BaseBusiness):
    __tablename__ = 'security_questions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer_hash: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    user: Mapped[UsersModel] = relationship("UsersModel", back_populates="security_questions")

    __table_args__ = (Index('idx_security_questions_user_id', 'user_id'),)


class TranslationOfficeDataModel(BaseBusiness):
    __tablename__ = 'translation_office_info'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    license_key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    reg_no: Mapped[Optional[str]] = mapped_column(Text)
    representative: Mapped[Optional[str]] = mapped_column(Text)
    manager: Mapped[Optional[str]] = mapped_column(Text)
    address: Mapped[Optional[str]] = mapped_column(Text)
    phone: Mapped[Optional[str]] = mapped_column(Text)
    email: Mapped[Optional[str]] = mapped_column(Text)
    website: Mapped[Optional[str]] = mapped_column(Text)
    whatsapp: Mapped[Optional[str]] = mapped_column(Text)
    instagram: Mapped[Optional[str]] = mapped_column(Text)
    telegram: Mapped[Optional[str]] = mapped_column(Text)
    other_media: Mapped[Optional[str]] = mapped_column(Text)
    open_hours: Mapped[Optional[str]] = mapped_column(Text)
    logo: Mapped[Optional[bytes]] = mapped_column(LargeBinary)
    map_url: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False
    )

    def to_dataclass(self) -> TranslationOfficeData:
        return TranslationOfficeData(
            id=self.id, license_key=self.license_key, name=self.name, reg_no=self.reg_no,
            representative=self.representative, manager=self.manager, address=self.address,
            phone=self.phone, email=self.email, website=self.website, whatsapp=self.whatsapp,
            instagram=self.instagram, telegram=self.telegram, other_media=self.other_media,
            open_hours=self.open_hours, logo=self.logo, map_url=self.map_url,
            created_at=self.created_at, updated_at=self.updated_at
        )


# ---------------------------------------------------------------------
# 👥 CUSTOMER DOMAIN
# ---------------------------------------------------------------------

class CustomerModel(BaseBusiness):
    __tablename__ = 'customers'

    # Changed Integer to Text to match IssuedInvoiceModel and standard National ID format
    national_id: Mapped[str] = mapped_column(Text, primary_key=True, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[str] = mapped_column(Text, nullable=False)
    telegram_id: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    passport_image: Mapped[str | None] = mapped_column(Text)

    companions: Mapped[list["CompanionModel"]] = relationship(
        "CompanionModel", back_populates="customer", cascade="all, delete-orphan"
    )

    # New relationship to Invoices
    invoices: Mapped[list["IssuedInvoiceModel"]] = relationship(
        "IssuedInvoiceModel", back_populates="customer"
    )

    __table_args__ = (
        Index('idx_customers_national_id', 'national_id'),
        Index('idx_customers_phone', 'phone'),
        Index('idx_customers_name', 'name'),
    )

    def __repr__(self) -> str:
        return f"<CustomerModel(national_id={self.national_id}, name={self.name!r})>"


class CompanionModel(BaseBusiness):
    __tablename__ = 'companions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    national_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    # Foreign Key to Customer
    customer_national_id: Mapped[str] = mapped_column(
        Text,  # Changed to Text to match CustomerModel
        ForeignKey('customers.national_id', ondelete="CASCADE"),
        nullable=False
    )

    customer: Mapped[CustomerModel] = relationship("CustomerModel", back_populates="companions")

    __table_args__ = (
        Index('idx_companions_national_id', 'national_id'),
        Index('idx_companions_customer_national_id', 'customer_national_id'),
        Index('idx_companions_name', 'name'),
    )


# ---------------------------------------------------------------------
# 🛠 SERVICES DOMAIN
# ---------------------------------------------------------------------

class ServicesModel(BaseBusiness):
    __tablename__ = 'services'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False, default="default")
    base_price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    default_page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Relationships
    dynamic_prices: Mapped[list["ServiceDynamicPrice"]] = relationship(
        back_populates="service", cascade="all, delete-orphan"
    )
    aliases: Mapped[list["ServiceAlias"]] = relationship(
        back_populates="service", cascade="all, delete-orphan"
    )
    # Inverse relationship for Invoice Items (optional but useful)
    invoice_items: Mapped[list["InvoiceItemModel"]] = relationship(
        "InvoiceItemModel", back_populates="service"
    )

    def __repr__(self) -> str:
        return f"<ServicesModel(id={self.id}, name={self.name!r})>"

    def to_dto(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "base_price": self.base_price,
            "default_page_count": self.default_page_count,
            "dynamic_prices": [dp.to_dto() for dp in self.dynamic_prices],
            "aliases": [a.to_dto() for a in self.aliases],
        }


class ServiceDynamicPrice(BaseBusiness):
    __tablename__ = 'service_dynamic_prices'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    service: Mapped["ServicesModel"] = relationship(back_populates="dynamic_prices")
    aliases: Mapped[list["ServiceDynamicPriceAlias"]] = relationship(
        back_populates="dynamic_price", cascade="all, delete-orphan"
    )

    def to_dto(self):
        return {
            "id": self.id,
            "service_id": self.service_id,
            "name": self.name,
            "unit_price": self.unit_price,
            "aliases": [a.to_dto() for a in self.aliases],
        }


class ServiceAlias(BaseBusiness):
    __tablename__ = 'service_aliases'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"))
    alias: Mapped[str] = mapped_column(Text, nullable=False)

    service: Mapped["ServicesModel"] = relationship(back_populates="aliases")

    def to_dto(self):
        return {
            "id": self.id,
            "service_id": self.service_id,
            "alias": self.alias,
        }


class ServiceDynamicPriceAlias(BaseBusiness):
    __tablename__ = 'service_dynamic_price_aliases'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dynamic_price_id: Mapped[int] = mapped_column(
        ForeignKey("service_dynamic_prices.id", ondelete="CASCADE"), nullable=False
    )
    alias: Mapped[str] = mapped_column(Text, nullable=False)

    dynamic_price: Mapped["ServiceDynamicPrice"] = relationship(back_populates="aliases")

    def to_dto(self):
        return {
            "id": self.id,
            "dynamic_price_id": self.dynamic_price_id,
            "alias": self.alias,
        }


class SmartSearchHistoryModel(BaseBusiness):
    __tablename__ = 'smart_search_history'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    def to_dto(self):
        return {
            "id": self.id,
            "entry": self.entry,
            "created_at": self.created_at,
        }


class FixedPricesModel(BaseBusiness):
    __tablename__ = 'fixed_prices'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)

    def to_dto(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
        }


class OtherServicesModel(BaseBusiness):
    __tablename__ = 'other_services'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)

    def to_dto(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
        }


# ---------------------------------------------------------------------
# 🧾 INVOICES DOMAIN (Central Hub)
# ---------------------------------------------------------------------

class IssuedInvoiceModel(BaseBusiness):
    __tablename__ = 'issued_invoices'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_number: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    name: Mapped[str] = mapped_column(Text, nullable=False)

    # ✅ LINKED: Foreign Key to Customers
    national_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("customers.national_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

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

    # ✅ LINKED: Foreign Key to Users
    username: Mapped[Optional[str]] = mapped_column(
        Text,
        ForeignKey("users.username", ondelete="SET NULL"),
        nullable=True
    )

    pdf_file_path: Mapped[Optional[str]] = mapped_column(Text)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    items: Mapped[List["InvoiceItemModel"]] = relationship(
        "InvoiceItemModel", cascade="all, delete-orphan", back_populates="invoice"
    )
    customer: Mapped["CustomerModel"] = relationship(
        "CustomerModel", back_populates="invoices"
    )
    user: Mapped["UsersModel"] = relationship(
        "UsersModel", back_populates="invoices"
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
            id=self.id, invoice_number=self.invoice_number, name=self.name,
            national_id=self.national_id, phone=self.phone, issue_date=self.issue_date,
            delivery_date=self.delivery_date, collection_date=self.collection_date,
            payment_date=self.payment_date, translator=self.translator,
            total_items=self.total_items, total_amount=self.total_amount,
            total_translation_price=self.total_translation_price,
            total_certified_copy_price=self.total_certified_copy_price,
            total_registration_price=self.total_registration_price,
            total_confirmation_price=self.total_confirmation_price,
            total_additional_issues_price=self.total_additional_issues_price,
            advance_payment=self.advance_payment, discount_amount=self.discount_amount,
            emergency_cost=self.emergency_cost, final_amount=self.final_amount,
            payment_status=self.payment_status, delivery_status=self.delivery_status,
            source_language=self.source_language, target_language=self.target_language,
            username=self.username, pdf_file_path=self.pdf_file_path, remarks=self.remarks,
        )

@event.listens_for(IssuedInvoiceModel, 'before_update', propagate=True)
def before_update_listener(mapper, connection, target):
    if target.delivery_status == 4 and target.collection_date is None:
        target.collection_date = datetime.now(timezone.utc)
    if target.payment_status == 1 and target.payment_date is None:
        target.payment_date = datetime.now(timezone.utc)


class DeletedInvoiceModel(BaseBusiness):
    """Archive table for deleted invoices."""
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
            id=self.id, invoice_number=self.invoice_number, name=self.name,
            national_id=self.national_id, phone=self.phone, issue_date=self.issue_date,
            delivery_date=self.delivery_date, collection_date=self.collection_date,
            payment_date=self.payment_date, translator=self.translator,
            total_items=self.total_items, total_amount=self.total_amount,
            total_translation_price=self.total_translation_price,
            total_certified_copy_price=self.total_certified_copy_price,
            total_registration_price=self.total_registration_price,
            total_confirmation_price=self.total_confirmation_price,
            total_additional_issues_price=self.total_additional_issues_price,
            final_amount=self.final_amount, username=self.username,
            remarks=self.remarks, deleted_at=self.deleted_at, deleted_by=self.deleted_by
        )


class EditedInvoiceModel(BaseBusiness):
    __tablename__ = "edited_invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_number: Mapped[str] = mapped_column(
        Text, ForeignKey("issued_invoices.invoice_number", ondelete="CASCADE"),
        nullable=False, index=True
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
        return EditedInvoiceData(
            id=self.id, invoice_number=self.invoice_number, edited_field=self.edited_field,
            old_value=self.old_value, new_value=self.new_value, edited_by=self.edited_by,
            edited_at=self.edited_at, remarks=self.remarks,
        )


class InvoiceItemModel(BaseBusiness):
    __tablename__ = 'invoice_items'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_number: Mapped[str] = mapped_column(
        Text, ForeignKey("issued_invoices.invoice_number", ondelete="CASCADE"),
        nullable=False
    )

    # ✅ LINKED: Foreign Key to Services
    service_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("services.id", ondelete="RESTRICT"),
        nullable=False
    )

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
    service: Mapped["ServicesModel"] = relationship(back_populates="invoice_items")

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
            id=self.id, invoice_number=self.invoice_number, service_id=self.service_id,
            service_name=self.service_name, quantity=self.quantity, page_count=self.page_count,
            additional_issues=self.additional_issues, is_official=self.is_official,
            has_judiciary_seal=self.has_judiciary_seal, has_foreign_affairs_seal=self.has_foreign_affairs_seal,
            dynamic_price_1=self.dynamic_price_1, dynamic_price_2=self.dynamic_price_2,
            dynamic_price_amount_1=self.dynamic_price_amount_1, dynamic_price_amount_2=self.dynamic_price_amount_2,
            remarks=self.remarks, translation_price=self.translation_price,
            certified_copy_price=self.certified_copy_price, registration_price=self.registration_price,
            judiciary_seal_price=self.judiciary_seal_price, foreign_affairs_seal_price=self.foreign_affairs_seal_price,
            additional_issues_price=self.additional_issues_price, total_price=self.total_price,
        )


class WorkspaceBatchModel(BaseBusiness):
    __tablename__ = "workspace_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_number: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    office_type: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    sent_by: Mapped[str] = mapped_column(Text, nullable=False)
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(Text, default="pending")
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    items: Mapped[List["WorkspaceBatchItemModel"]] = relationship(
        "WorkspaceBatchItemModel", cascade="all, delete-orphan", back_populates="batch"
    )

    __table_args__ = (
        Index('idx_workspace_batches_office_type', 'office_type'),
        Index('idx_workspace_batches_status', 'status'),
        Index('idx_workspace_batches_created_at', 'created_at'),
    )

    def to_dataclass(self) -> WorkspaceBatchData:
        return WorkspaceBatchData(
            id=self.id, batch_number=self.batch_number, office_type=self.office_type,
            created_at=self.created_at, sent_by=self.sent_by, received_at=self.received_at,
            status=self.status, remarks=self.remarks
        )


class WorkspaceBatchItemModel(BaseBusiness):
    __tablename__ = "workspace_batch_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("workspace_batches.id", ondelete="CASCADE"), nullable=False)
    invoice_item_id: Mapped[int] = mapped_column(ForeignKey("invoice_items.id", ondelete="CASCADE"), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approval_status: Mapped[str] = mapped_column(Text, default="pending")
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    batch: Mapped["WorkspaceBatchModel"] = relationship(back_populates="items")
    invoice_item: Mapped["InvoiceItemModel"] = relationship()

    __table_args__ = (
        Index('idx_workspace_batch_items_batch_id', 'batch_id'),
        Index('idx_workspace_batch_items_status', 'approval_status'),
        Index('idx_workspace_batch_items_invoice_item', 'invoice_item_id'),
    )

    def to_dataclass(self) -> WorkspaceBatchItemData:
        return WorkspaceBatchItemData(
            id=self.id, batch_id=self.batch_id, invoice_item_id=self.invoice_item_id,
            sent_at=self.sent_at, approved_at=self.approved_at,
            approval_status=self.approval_status, remarks=self.remarks
        )


class WorkspaceQuotaModel(BaseBusiness):
    __tablename__ = "workspace_quotas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    office_type: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    max_daily: Mapped[int] = mapped_column(Integer, default=0)
    max_weekly: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)
    )

    __table_args__ = (Index('idx_workspace_quotas_office_type', 'office_type'),)

    def to_dataclass(self) -> WorkspaceQuotaData:
        return WorkspaceQuotaData(
            id=self.id, office_type=self.office_type, max_daily=self.max_daily,
            max_weekly=self.max_weekly, updated_at=self.updated_at
        )

# ---------------------------------------------------------------------
# 💸 EXPENSES DOMAIN
# ---------------------------------------------------------------------

class ExpenseModel(BaseBusiness):
    __tablename__ = 'expenses'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)  # Description
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)

    # ✅ LINKED: Foreign Key to Users (Audit trail: who created this?)
    # We use SET NULL so if a user is deleted, the financial record remains.
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Relationships
    user: Mapped["UsersModel"] = relationship("UsersModel", back_populates="expenses")

    __table_args__ = (
        CheckConstraint(
            "category IN ('Salary', 'Rent', 'Utilities', 'Office Supplies', 'Other')",
            name='check_expense_category'
        ),
        Index('idx_expenses_date', 'expense_date'),
        Index('idx_expenses_category', 'category'),
        Index('idx_expenses_user_id', 'user_id'),
    )

    def __repr__(self) -> str:
        return f"<ExpenseModel(name={self.name!r}, amount={self.amount}, date={self.expense_date})>"
