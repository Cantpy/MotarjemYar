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
from sqlalchemy import (
    ForeignKey, Integer, Text, Index, CheckConstraint,
    LargeBinary, DateTime, func, String
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base

BaseUsers = declarative_base()


class UsersModel(BaseUsers):
    """
    Core user authentication and authorization model.
    This model is self-contained and does not link to other domains.
    """
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Authentication
    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_hash: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    # Authorization
    role: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # UI Personalization
    display_name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="User's preferred display name for UI (e.g., nickname, 'Mr. Smith')"
    )
    avatar_path: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Optional path to user's profile picture"
    )

    # Access control
    start_date: Mapped[str | None] = mapped_column(Text)
    end_date: Mapped[str | None] = mapped_column(Text)

    # Session management
    token_hash: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[str | None] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[str | None] = mapped_column(Text)

    # Security
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, server_default='0'
    )
    lockout_until_utc: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 🔑 Relationships
    login_logs: Mapped[list["LoginLogsModel"]] = relationship(
        "LoginLogsModel",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    security_questions: Mapped[list["SecurityQuestionModel"]] = relationship(
        "SecurityQuestionModel",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    edited_logs: Mapped[list["EditedUsersLogModel"]] = relationship(
        "EditedUsersLogModel",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    deleted_records: Mapped[list["DeletedUsersModel"]] = relationship(
        "DeletedUsersModel",
        primaryjoin="UsersModel.id == foreign(DeletedUsersModel.original_user_id)",
        back_populates="user",
        viewonly=True
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'translator', 'clerk', 'accountant')",
            name='check_role'
        ),
        CheckConstraint(
            "active IN (0, 1)",
            name='check_active'
        ),
        Index('idx_users_active', 'active'),
        Index('idx_users_role', 'role'),
        Index('idx_users_token', 'token_hash'),
        Index('idx_users_username', 'username'),
        # --- REMOVED: Index for employee_id ---
    )

    def __repr__(self) -> str:
        return (f"<UsersModel(id={self.id}, username={self.username!r}, "
                f"display_name={self.display_name!r}, role={self.role!r})>")


class EditedUsersLogModel(BaseUsers):
    # ... (This class remains unchanged)
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
    """
    Soft-delete archive for users removed from the system.
    Preserves essential information for audit trails and compliance.
    """
    __tablename__ = "deleted_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    original_user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    # --- REMOVED: The employee_id reference ---

    username: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100))
    role: Mapped[str | None] = mapped_column(Text)
    deleted_by: Mapped[str] = mapped_column(Text, nullable=False)
    deleted_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.current_timestamp(),
        nullable=False
    )

    user: Mapped[UsersModel | None] = relationship(
        "UsersModel",
        primaryjoin="UsersModel.id == foreign(DeletedUsersModel.original_user_id)",
        back_populates="deleted_records",
        viewonly=True
    )

    __table_args__ = (
        Index("idx_deleted_users_original_id", "original_user_id"),
        Index("idx_deleted_users_username", "username"),
        # --- REMOVED: Index for employee_id ---
        Index("idx_deleted_users_deleted_at", "deleted_at"),
    )

    def __repr__(self) -> str:
        return (f"<DeletedUsersModel(id={self.id}, original_user_id={self.original_user_id}, "
                f"username='{self.username}', deleted_by='{self.deleted_by}')>")


class LoginLogsModel(BaseUsers):
    # ... (This class remains unchanged)
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
    # ... (This class remains unchanged)
    __tablename__ = 'translation_office'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    license_key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
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
    logo: Mapped[bytes | None] = mapped_column(LargeBinary)
    map_url: Mapped[str | None] = mapped_column(Text)
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
    __table_args__ = (
        Index('idx_translation_office_license_key', 'license_key'),
    )

    def __repr__(self) -> str:
        return f"<TranslationOfficeDataModel(id={self.id}, name={self.name!r})>"


class SecurityQuestionModel(BaseUsers):
    # ... (This class remains unchanged)
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
