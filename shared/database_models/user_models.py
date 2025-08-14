from __future__ import annotations
from sqlalchemy import Column, Integer, Text, Index, CheckConstraint, LargeBinary, Date, DateTime, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base

BaseUsers = declarative_base()


class UsersModel(BaseUsers):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_hash: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[int] = mapped_column(Integer, default=1)
    start_date: Mapped[str | None] = mapped_column(Text)
    end_date: Mapped[str | None] = mapped_column(Text)
    token_hash: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[str | None] = mapped_column(Text)

    user_profile: Mapped[UserProfileModel | None] = relationship(
        "UserProfileModel",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    login_logs: Mapped[list[LoginLogsModel]] = relationship(
        "LoginLogsModel",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    issued_invoices: Mapped[list["IssuedInvoiceModel"]] = relationship(
        "IssuedInvoiceModel",
        back_populates="user",
        viewonly=True,  # invoices live in another DB; keep as logical relationship only
    )

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'translator', 'clerk', 'accountant')", name='check_role'),
        Index('idx_users_active', 'active'),
        Index('idx_users_role', 'role'),
        Index('idx_users_token', 'token_hash'),
        Index('idx_users_username', 'username'),
    )

    def __repr__(self) -> str:
        return f"<UsersModel(id={self.id}, username={self.username!r}, role={self.role!r})>"


class UserProfileModel(BaseUsers):
    __tablename__ = 'user_profiles'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    role_fa: Mapped[str] = mapped_column(Text, nullable=False)
    date_of_birth: Mapped[Date | None] = mapped_column(Date)
    email: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(Text)
    national_id: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    bio: Mapped[str | None] = mapped_column(Text)
    avatar_path: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[str | None] = mapped_column(Text)

    user: Mapped[UsersModel] = relationship("UsersModel", back_populates="user_profile")

    __table_args__ = (
        Index('idx_profiles_username', 'username'),
    )

    def __repr__(self) -> str:
        return f"<UserProfileModel(id={self.id}, username={self.username!r}, full_name={self.full_name!r})>"


class LoginLogsModel(BaseUsers):
    __tablename__ = 'login_logs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(Text, nullable=False)
    login_time: Mapped[str | None] = mapped_column(Text)
    logout_time: Mapped[str | None] = mapped_column(Text)
    time_on_app: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(Text)
    user_agent: Mapped[str | None] = mapped_column(Text)

    user: Mapped[UsersModel] = relationship("UsersModel", back_populates="login_logs")

    __table_args__ = (
        CheckConstraint("status IN ('success', 'failed', 'auto_login_success')", name='check_status'),
        Index('idx_login_logs_status', 'status'),
        Index('idx_login_logs_time', 'login_time'),
        Index('idx_login_logs_username', 'username'),
    )

    def __repr__(self) -> str:
        return f"<LoginLogsModel(id={self.id}, username={self.username!r}, login_time={self.login_time!r})>"


class TranslationOfficeDataModel(BaseUsers):
    __tablename__ = 'translation_office'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    reg_no: Mapped[str | None] = mapped_column(Text)
    representative: Mapped[str | None] = mapped_column(Text)
    manager: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(Text)
    whatsapp: Mapped[str | None] = mapped_column(Text)
    instagram: Mapped[str | None] = mapped_column(Text)
    telegram: Mapped[str | None] = mapped_column(Text)
    other_media: Mapped[str | None] = mapped_column(Text)
    open_hours: Mapped[str | None] = mapped_column(Text)
    map_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.current_timestamp())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=func.current_timestamp())

    def __repr__(self) -> str:
        return f"<TranslationOfficeDataModel(id={self.id}, name={self.name!r})>"
