from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, Boolean,
    ForeignKey, CheckConstraint, UniqueConstraint, Index,
    LargeBinary, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


# ============================================================================
# CUSTOMERS DATABASE MODELS
# ============================================================================

class CustomerModel(Base):
    __tablename__ = 'customers'

    national_id = Column(Text, primary_key=True, unique=True, nullable=False)
    name = Column(Text, nullable=False)
    phone = Column(Text, nullable=False)
    telegram_id = Column(Text)
    email = Column(Text)
    address = Column(Text)
    passport_image = Column(Text)

    # Relationships
    companions = relationship("CompanionModel", back_populates="customer", cascade="all, delete-orphan")
    invoices = relationship("IssuedInvoiceModel", back_populates="customer")

    # Indexes
    __table_args__ = (
        Index('idx_customers_national_id', 'national_id'),
    )


class CompanionModel(Base):
    __tablename__ = 'companions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    national_id = Column(Text, nullable=False, unique=True)
    customer_national_id = Column(Text, ForeignKey('customers.national_id', ondelete='CASCADE'), nullable=False)

    # Relationships
    customer = relationship("CustomerModel", back_populates="companions")


# ============================================================================
# INVOICES DATABASE MODELS
# ============================================================================

class IssuedInvoiceModel(Base):
    __tablename__ = 'issued_invoices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(Integer, nullable=False, unique=True)
    name = Column(Text, nullable=False)
    national_id = Column(Text, ForeignKey("customers.national_id"), nullable=False)
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
    username = Column(Text, ForeignKey('users.username'))
    pdf_file_path = Column(Text)

    # Relationships
    invoice_items = relationship("InvoiceItemModel", back_populates="issued_invoice", cascade="all, delete-orphan")
    customer = relationship("CustomerModel", back_populates="invoices")
    user = relationship("UsersModel", foreign_keys=[username],
                        primaryjoin="IssuedInvoiceModel.username == UsersModel.username")

    # Constraints
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


class InvoiceItemModel(Base):
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
    issued_invoice = relationship("IssuedInvoiceModel", back_populates="invoice_items")

    # Constraints
    __table_args__ = (
        CheckConstraint('officiality IN (0, 1)', name='check_officiality'),
        CheckConstraint('judiciary_seal IN (0, 1)', name='check_judiciary_seal'),
        CheckConstraint('foreign_affairs_seal IN (0, 1)', name='check_foreign_affairs_seal'),
        Index('idx_invoice_items_foreign', 'foreign_affairs_seal'),
        Index('idx_invoice_items_invoice_id', 'invoice_number'),
        Index('idx_invoice_items_judiciary', 'judiciary_seal'),
        Index('idx_invoice_items_official', 'officiality'),
    )


# ============================================================================
# SERVICES DATABASE MODELS
# ============================================================================

class ServicesModel(Base):
    __tablename__ = 'services'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    base_price = Column(Integer)
    dynamic_price_name_1 = Column(Text)
    dynamic_price_1 = Column(Integer)
    dynamic_price_name_2 = Column(Text)
    dynamic_price_2 = Column(Integer)


class FixedPricesModel(Base):
    __tablename__ = 'fixed_prices'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    price = Column(Integer, nullable=False)
    is_default = Column(Boolean, nullable=False)
    label_name = Column(Text)


class OtherServicesModel(Base):
    __tablename__ = 'other_services'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    price = Column(Integer, nullable=False)


# ============================================================================
# USERS DATABASE MODELS
# ============================================================================

class UsersModel(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(Text, nullable=False, unique=True)
    password_hash = Column(LargeBinary, nullable=False)
    role = Column(Text, nullable=False)
    active = Column(Integer, default=1)
    start_date = Column(Text)
    end_date = Column(Text)
    token_hash = Column(Text)
    expires_at = Column(Text)
    created_at = Column(Text)
    updated_at = Column(Text)

    # Relationships
    user_profile = relationship("UserProfileModel", back_populates="user", uselist=False, cascade="all, delete-orphan")
    login_logs = relationship("LoginLogsModel", back_populates="user", cascade="all, delete-orphan")
    issued_invoices = relationship("IssuedInvoiceModel", back_populates="user")

    # Constraints
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'translator', 'clerk', 'accountant')", name='check_role'),
        Index('idx_users_active', 'active'),
        Index('idx_users_role', 'role'),
        Index('idx_users_token', 'token_hash'),
        Index('idx_users_username', 'username'),
    )


class UserProfileModel(Base):
    __tablename__ = 'user_profiles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(Text, ForeignKey('users.username', ondelete='CASCADE'), nullable=False, unique=True)
    full_name = Column(Text, nullable=False)
    role_fa = Column(Text, nullable=False)
    date_of_birth = Column(Date)
    email = Column(Text)
    phone = Column(Text)
    national_id = Column(Text)
    address = Column(Text)
    bio = Column(Text)
    avatar_path = Column(Text)
    created_at = Column(Text)
    updated_at = Column(Text)

    # Relationships
    user = relationship("UsersModel", back_populates="user_profile")

    # Indexes
    __table_args__ = (
        Index('idx_profiles_username', 'username'),
    )


class LoginLogsModel(Base):
    __tablename__ = 'login_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(Text, ForeignKey('users.username', ondelete='CASCADE'), nullable=False)
    login_time = Column(Text)
    logout_time = Column(Text)
    time_on_app = Column(Integer)
    status = Column(Text)
    ip_address = Column(Text)
    user_agent = Column(Text)

    # Relationships
    user = relationship("UsersModel", back_populates="login_logs")

    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('success', 'failed', 'auto_login_success')", name='check_status'),
        Index('idx_login_logs_status', 'status'),
        Index('idx_login_logs_time', 'login_time'),
        Index('idx_login_logs_username', 'username'),
    )


class TranslationOfficeDataModl(Base):
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
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())


# ============================================================================
# DATABASE CONFIGURATION EXAMPLE
# ============================================================================

"""
Example usage for multiple databases:

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database engines
customers_engine = create_engine('sqlite:///customers.db')
invoices_engine = create_engine('sqlite:///invoices.db')
services_engine = create_engine('sqlite:///services.db')
users_engine = create_engine('sqlite:///users.db')

# Create tables
CustomerModel.metadata.create_all(customers_engine)
CompanionModel.metadata.create_all(customers_engine)

IssuedInvoiceModel.metadata.create_all(invoices_engine)
InvoiceItemModel.metadata.create_all(invoices_engine)

ServicesModel.metadata.create_all(services_engine)
FixedPricesModel.metadata.create_all(services_engine)
OtherServicesModel.metadata.create_all(services_engine)

UsersModel.metadata.create_all(users_engine)
UserProfileModel.metadata.create_all(users_engine)
LoginLogsModel.metadata.create_all(users_engine)
TranslationOfficeDataModl.metadata.create_all(users_engine)

# Session makers
CustomersSession = sessionmaker(bind=customers_engine)
InvoicesSession = sessionmaker(bind=invoices_engine)
ServicesSession = sessionmaker(bind=services_engine)
UsersSession = sessionmaker(bind=users_engine)

# Usage example
customers_session = CustomersSession()
customer = customers_session.query(CustomerModel).filter_by(national_id='۴۲۱۰۳۴۲۰۳۳').first()
print(f"CustomerModel: {customer.name}")
customers_session.close()
"""
