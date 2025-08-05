from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import json

Base = declarative_base()


@dataclass
class InvoiceItemData:
    item_name: str
    item_qty: int
    item_price: int
    officiality: int
    judiciary_seal: int
    foreign_affairs_seal: int
    remarks: Optional[str]


@dataclass
class InvoiceData:
    invoice_number: int
    name: str
    national_id: int
    phone: str
    issue_date: str
    delivery_date: str
    translator: str
    total_items: Optional[int]
    total_amount: int
    total_translation_price: int
    advance_payment: int
    discount_amount: int
    force_majeure: int
    final_amount: int
    payment_status: int
    delivery_status: int
    total_official_docs_count: int
    total_unofficial_docs_count: int
    total_pages_count: int
    total_judiciary_count: int
    total_foreign_affairs_count: int
    total_additional_doc_count: int
    source_language: Optional[str]
    target_language: Optional[str]
    remarks: Optional[str]
    username: Optional[str]
    pdf_file_path: Optional[str]
    items: List[InvoiceItemData]


@dataclass
class InvoiceSummary:
    """Data class for invoice summary statistics"""
    total_count: int
    total_amount: float
    translator_stats: List[tuple]


@dataclass
class DocumentCount:
    """Data class for document count information"""
    invoice_number: str
    count: int


class IssuedInvoice(Base):
    """SQLAlchemy model for issued_invoices"""
    __tablename__ = 'issued_invoices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(Integer, unique=True, nullable=False)
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

    payment_status = Column(Integer, default=0)  # CHECK IN (0, 1)
    delivery_status = Column(Integer, default=0)  # CHECK IN (0, 1, 2, 3, 4)

    total_official_docs_count = Column(Integer, default=0)
    total_unofficial_docs_count = Column(Integer, default=0)
    total_pages_count = Column(Integer, default=0)
    total_judiciary_count = Column(Integer, default=0)
    total_foreign_affairs_count = Column(Integer, default=0)
    total_additional_doc_count = Column(Integer, default=0)

    source_language = Column(Text)
    target_language = Column(Text)
    remarks = Column(Text)

    username = Column(Text)  # FK to users.username, not enforced in SQLAlchemy yet
    pdf_file_path = Column(Text)

    items = relationship("InvoiceItemModel", back_populates="invoice", cascade="all, delete-orphan",
                         primaryjoin="IssuedInvoiceModel.invoice_number==InvoiceItemModel.invoice_number")

    def to_dataclass(self) -> InvoiceData:
        """Convert SQLAlchemy model to InvoiceData dataclass"""
        return InvoiceData(
            invoice_number=self.invoice_number,
            name=self.name,
            national_id=self.national_id,
            phone=self.phone,
            issue_date=self.issue_date.strftime('%Y-%m-%d') if self.issue_date else None,
            delivery_date=self.delivery_date.strftime('%Y-%m-%d') if self.delivery_date else None,
            translator=self.translator,
            total_items=self.total_items,
            total_amount=self.total_amount,
            total_translation_price=self.total_translation_price,
            advance_payment=self.advance_payment,
            discount_amount=self.discount_amount,
            force_majeure=self.force_majeure,
            final_amount=self.final_amount,
            payment_status=self.payment_status,
            delivery_status=self.delivery_status,
            total_official_docs_count=self.total_official_docs_count,
            total_unofficial_docs_count=self.total_unofficial_docs_count,
            total_pages_count=self.total_pages_count,
            total_judiciary_count=self.total_judiciary_count,
            total_foreign_affairs_count=self.total_foreign_affairs_count,
            total_additional_doc_count=self.total_additional_doc_count,
            source_language=self.source_language,
            target_language=self.target_language,
            remarks=self.remarks,
            username=self.username,
            pdf_file_path=self.pdf_file_path,
            items=[item.to_dataclass() for item in self.items]
        )


class InvoiceItem(Base):
    __tablename__ = 'invoice_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(Integer, ForeignKey("issued_invoices.invoice_number", ondelete="CASCADE"), nullable=False)
    item_name = Column(Text, nullable=False)
    item_qty = Column(Integer, default=1, nullable=False)
    item_price = Column(Integer, nullable=False)
    officiality = Column(Integer, default=0)
    judiciary_seal = Column(Integer, default=0)
    foreign_affairs_seal = Column(Integer, default=0)
    remarks = Column(Text)

    invoice = relationship("IssuedInvoiceModel", back_populates="items")

    def get_document_count(self) -> int:
        """Returns the number of documents represented by this invoice item"""
        return self.item_qty or 1

    def to_dataclass(self) -> InvoiceItemData:
        return InvoiceItemData(
            item_name=self.item_name,
            item_qty=self.item_qty,
            item_price=self.item_price,
            officiality=self.officiality,
            judiciary_seal=self.judiciary_seal,
            foreign_affairs_seal=self.foreign_affairs_seal,
            remarks=self.remarks
        )


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)  # admin, translator, etc.
    active = Column(Boolean, default=True)

    start_date = Column(String)
    end_date = Column(String)

    token_hash = Column(String)
    expires_at = Column(String)

    created_at = Column(String)
    updated_at = Column(String)

    profile = relationship("UserProfileModel", back_populates="user", uselist=False)
    logs = relationship("LoginLogsModel", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = 'user_profiles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), ForeignKey('users.username'), nullable=False, unique=True)

    full_name = Column(String(100), nullable=False)
    role_fa = Column(String, nullable=False)
    date_of_birth = Column(String)
    email = Column(String)
    phone = Column(String)
    national_id = Column(String)
    address = Column(String)
    bio = Column(Text)
    avatar_path = Column(Text)

    created_at = Column(String)
    updated_at = Column(String)

    user = relationship("UsersModel", back_populates="profile")


class LoginLog(Base):
    __tablename__ = 'login_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, ForeignKey('users.username', ondelete="CASCADE"), nullable=False)

    login_time = Column(String)
    logout_time = Column(String)
    time_on_app = Column(Integer)
    status = Column(String)  # success, failed, auto_login_success
    ip_address = Column(String)
    user_agent = Column(String)

    user = relationship("UsersModel", back_populates="logs")


class TranslationOffice(Base):
    __tablename__ = 'translation_office'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    reg_no = Column(Text)
    representative = Column(Text)
    manager = Column(Text)
    address = Column(Text)
    phone = Column(Text)
    website = Column(Text)
    whatsapp = Column(Text)
    instagram = Column(Text)
    telegram = Column(Text)
    other_media = Column(Text)
    open_hours = Column(Text)
    map_url = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InvoiceFilter:
    """Class for managing invoice filtering criteria"""

    def __init__(self):
        self.search_text: str = ""
        self.visible_columns: List[bool] = [True] * 10

    def set_search_text(self, text: str):
        """Set search text filter"""
        self.search_text = text.lower()

    def set_column_visibility(self, column_index: int, visible: bool):
        """Set column visibility"""
        if 0 <= column_index < len(self.visible_columns):
            self.visible_columns[column_index] = visible

    def matches_search(self, invoice: InvoiceData) -> bool:
        """Check if invoice matches search criteria"""
        if not self.search_text:
            return True

        searchable_fields = [
            invoice.invoice_number,
            invoice.name,
            invoice.national_id,
            invoice.phone,
            invoice.translator
        ]

        return any(self.search_text in str(field).lower() for field in searchable_fields)


class ColumnSettings:
    """Class for managing column visibility settings"""

    COLUMN_NAMES = [
        "شماره فاکتور", "نام", "کد ملی", "شماره تماس", "تاریخ صدور",
        "تاریخ تحویل", "مترجم", "تعداد اسناد", "هزیته فاکتور", "مشاهده فاکتور"
    ]

    def __init__(self):
        self.visible_columns = [True] * len(self.COLUMN_NAMES)

    def get_column_name(self, index: int) -> str:
        """Get column name by index"""
        if 0 <= index < len(self.COLUMN_NAMES):
            return self.COLUMN_NAMES[index]
        return ""

    def set_column_visible(self, index: int, visible: bool):
        """Set column visibility"""
        if 0 <= index < len(self.visible_columns):
            self.visible_columns[index] = visible

    def is_column_visible(self, index: int) -> bool:
        """Check if column is visible"""
        if 0 <= index < len(self.visible_columns):
            return self.visible_columns[index]
        return False
