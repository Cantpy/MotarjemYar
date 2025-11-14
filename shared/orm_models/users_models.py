# shared/orm_models/users_models.py

"""
Users SQLAlchemy models with clear separation from payroll domain.
Includes:
- UsersModel (core authentication and authorization)
- EditedUsersLogModel (audit trail for user changes)
- DeletedUsersModel (soft-delete archive)
- LoginLogsModel (login/logout tracking)
- SecurityQuestionModel (password recovery)
- TranslationOfficeDataModel (office configuration)

Key changes:
- Removed UserProfileModel entirely (employee data lives in payroll DB)
- Added display_name to UsersModel for UI personalization
- Optional avatar_path for profile pictures
- REMOVED: employee_id link to the payroll database's EmployeeModel
"""

from __future__ import annotations
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
from sqlalchemy import (
    ForeignKey, Integer, Text, Index, CheckConstraint,
    LargeBinary, DateTime, func, String
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base

BaseUsers = declarative_base()


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


class UsersModel(BaseUsers):
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

    # --- Relationship definitions ---
    edited_logs: Mapped[list["EditedUsersLogModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    deleted_records: Mapped[list["DeletedUsersModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    login_logs: Mapped[list["LoginLogsModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    security_questions: Mapped[list["SecurityQuestionModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<UsersModel(id={self.id}, username={self.username!r}, role={self.role!r})>"


class EditedUsersLogModel(BaseUsers):
    __tablename__ = "edited_users_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    editor_username: Mapped[str] = mapped_column(Text, nullable=False)
    field_name: Mapped[str] = mapped_column(Text, nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.current_timestamp(),
        nullable=False
    )
    user: Mapped[UsersModel] = relationship(
        "UsersModel",
        back_populates="edited_logs"
    )
    __table_args__ = (
        Index("idx_edited_users_user_id", "user_id"),
        Index("idx_edited_users_field_name", "field_name"),
        Index("idx_edited_users_changed_at", "changed_at"),
    )

    def __repr__(self) -> str:
        return (f"<EditedUsersLogModel(id={self.id}, user_id={self.user_id}, "
                f"field='{self.field_name}', changed_at='{self.changed_at}')>")


class DeletedUsersModel(BaseUsers):
    __tablename__ = "deleted_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ✅ FIX: add ForeignKey to link this column to UsersModel.id
    original_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )

    username: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    role: Mapped[Optional[str]] = mapped_column(Text)
    deleted_by: Mapped[str] = mapped_column(Text, nullable=False)
    deleted_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.current_timestamp(),
        nullable=False
    )

    user: Mapped[Optional["UsersModel"]] = relationship(
        "UsersModel",
        back_populates="deleted_records"
    )

    __table_args__ = (
        Index("idx_deleted_users_original_id", "original_user_id"),
        Index("idx_deleted_users_username", "username"),
        Index("idx_deleted_users_deleted_at", "deleted_at"),
    )

    def __repr__(self) -> str:
        return (f"<DeletedUsersModel(id={self.id}, original_user_id={self.original_user_id}, "
                f"username='{self.username}', deleted_by='{self.deleted_by}')>")


class LoginLogsModel(BaseUsers):
    __tablename__ = 'login_logs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    login_time: Mapped[str | None] = mapped_column(Text)
    logout_time: Mapped[str | None] = mapped_column(Text)
    time_on_app: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(Text)
    user_agent: Mapped[str | None] = mapped_column(Text)
    user: Mapped[UsersModel] = relationship(
        "UsersModel",
        back_populates="login_logs"
    )
    __table_args__ = (
        CheckConstraint(
            "status IN ('success', 'failed', 'auto_login_success')",
            name='check_status'
        ),
        Index('idx_login_logs_user_id', 'user_id'),
        Index('idx_login_logs_status', 'status'),
        Index('idx_login_logs_time', 'login_time'),
    )

    def __repr__(self) -> str:
        return (f"<LoginLogsModel(id={self.id}, user_id={self.user_id}, "
                f"login_time={self.login_time!r}, status={self.status!r})>")


class TranslationOfficeDataModel(BaseUsers):
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.current_timestamp(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<TranslationOfficeDataModel(id={self.id}, name={self.name!r})>"

    def to_dataclass(self) -> "TranslationOfficeData":
        return TranslationOfficeData(
            id=self.id,
            license_key=self.license_key,
            name=self.name,
            reg_no=self.reg_no,
            representative=self.representative,
            manager=self.manager,
            address=self.address,
            phone=self.phone,
            email=self.email,
            website=self.website,
            whatsapp=self.whatsapp,
            instagram=self.instagram,
            telegram=self.telegram,
            other_media=self.other_media,
            open_hours=self.open_hours,
            logo=self.logo,
            map_url=self.map_url,
            created_at=self.created_at,
            updated_at=self.updated_at
        )


class SecurityQuestionModel(BaseUsers):
    __tablename__ = 'security_questions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer_hash: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    user: Mapped[UsersModel] = relationship(
        "UsersModel",
        back_populates="security_questions"
    )
    __table_args__ = (
        Index('idx_security_questions_user_id', 'user_id'),
    )

    def __repr__(self) -> str:
        return (f"<SecurityQuestionModel(id={self.id}, user_id={self.user_id}, "
                f"question='{self.question[:30]}...')>")
