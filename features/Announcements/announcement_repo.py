"""
Database _repository using SQLAlchemy ORM for SMS and Email notifications.
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.sql import and_, or_
from features.Announcements.announcement_models import (SMSNotification, EmailNotification, EmailAttachment,
                                                        NotificationStatus, NotificationFilter)
from shared.utils.path_utils import get_resource_path

announcements_db_path = get_resource_path("databases", "announcements.db")

Base = declarative_base()


class SMSNotificationORM(Base):
    """SQLAlchemy ORM model for SMS notifications."""
    __tablename__ = 'sms_notifications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipient_name = Column(String(255), nullable=False)
    recipient_phone = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    provider_message_id = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class EmailNotificationORM(Base):
    """SQLAlchemy ORM model for Email notifications."""
    __tablename__ = 'email_notifications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    provider_message_id = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationship with attachments
    attachments = relationship("EmailAttachmentORM", back_populates="email", cascade="all, delete-orphan")


class EmailAttachmentORM(Base):
    """SQLAlchemy ORM model for Email attachments."""
    __tablename__ = 'email_attachments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_id = Column(Integer, ForeignKey('email_notifications.id'), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    mime_type = Column(String(100), nullable=True)

    # Relationship with email
    email = relationship("EmailNotificationORM", back_populates="attachments")


class NotificationRepository:
    """Repository class for managing SMS and Email notifications."""

    def __init__(self, database_url: str = f"sqlite:///{announcements_db_path}"):
        """Initialize _repository with database connection."""
        self.engine = create_engine(database_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def _get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()

    # SMS Repository Methods
    def save_sms(self, sms: SMSNotification) -> SMSNotification:
        """Save SMS notification to database."""
        with self._get_session() as session:
            if sms.id:
                # Update existing
                db_sms = session.query(SMSNotificationORM).filter(SMSNotificationORM.id == sms.id).first()
                if db_sms:
                    for key, value in sms.to_dict().items():
                        if key != 'id' and value is not None:
                            if key in ['sent_at', 'delivered_at', 'created_at', 'updated_at'] and isinstance(value,
                                                                                                             str):
                                value = datetime.fromisoformat(value)
                            setattr(db_sms, key, value)
                    db_sms.updated_at = datetime.now()
                    session.commit()
                    session.refresh(db_sms)
                    return self._convert_sms_orm_to_model(db_sms)
            else:
                # Create new
                sms_data = sms.to_dict()
                del sms_data['id']  # Remove id for new records
                # Convert datetime strings back to datetime objects
                for key in ['sent_at', 'delivered_at', 'created_at', 'updated_at']:
                    if sms_data.get(key) and isinstance(sms_data[key], str):
                        sms_data[key] = datetime.fromisoformat(sms_data[key])

                db_sms = SMSNotificationORM(**sms_data)
                session.add(db_sms)
                session.commit()
                session.refresh(db_sms)
                return self._convert_sms_orm_to_model(db_sms)

    def get_sms_by_id(self, sms_id: int) -> Optional[SMSNotification]:
        """Get SMS notification by ID."""
        with self._get_session() as session:
            db_sms = session.query(SMSNotificationORM).filter(SMSNotificationORM.id == sms_id).first()
            return self._convert_sms_orm_to_model(db_sms) if db_sms else None

    def get_sms_list(self, filter_criteria: NotificationFilter = None, limit: int = 100, offset: int = 0) -> List[
        SMSNotification]:
        """Get filtered list of SMS notifications."""
        with self._get_session() as session:
            query = session.query(SMSNotificationORM)

            if filter_criteria and not filter_criteria.is_empty():
                conditions = []

                if filter_criteria.search_text:
                    search_term = f"%{filter_criteria.search_text}%"
                    conditions.append(
                        or_(
                            SMSNotificationORM.recipient_name.ilike(search_term),
                            SMSNotificationORM.recipient_phone.ilike(search_term),
                            SMSNotificationORM.message.ilike(search_term)
                        )
                    )

                if filter_criteria.status:
                    conditions.append(SMSNotificationORM.status == filter_criteria.status)

                if filter_criteria.date_from:
                    conditions.append(SMSNotificationORM.created_at >= filter_criteria.date_from)

                if filter_criteria.date_to:
                    conditions.append(SMSNotificationORM.created_at <= filter_criteria.date_to)

                if filter_criteria.recipient_filter:
                    recipient_term = f"%{filter_criteria.recipient_filter}%"
                    conditions.append(
                        or_(
                            SMSNotificationORM.recipient_name.ilike(recipient_term),
                            SMSNotificationORM.recipient_phone.ilike(recipient_term)
                        )
                    )

                if conditions:
                    query = query.filter(and_(*conditions))

            query = query.order_by(SMSNotificationORM.created_at.desc())
            db_sms_list = query.offset(offset).limit(limit).all()

            return [self._convert_sms_orm_to_model(db_sms) for db_sms in db_sms_list]

    def get_sms_count(self, filter_criteria: NotificationFilter = None) -> int:
        """Get count of SMS notifications matching filter."""
        with self._get_session() as session:
            query = session.query(SMSNotificationORM)

            if filter_criteria and not filter_criteria.is_empty():
                conditions = []

                if filter_criteria.search_text:
                    search_term = f"%{filter_criteria.search_text}%"
                    conditions.append(
                        or_(
                            SMSNotificationORM.recipient_name.ilike(search_term),
                            SMSNotificationORM.recipient_phone.ilike(search_term),
                            SMSNotificationORM.message.ilike(search_term)
                        )
                    )

                if filter_criteria.status:
                    conditions.append(SMSNotificationORM.status == filter_criteria.status)

                if filter_criteria.date_from:
                    conditions.append(SMSNotificationORM.created_at >= filter_criteria.date_from)

                if filter_criteria.date_to:
                    conditions.append(SMSNotificationORM.created_at <= filter_criteria.date_to)

                if filter_criteria.recipient_filter:
                    recipient_term = f"%{filter_criteria.recipient_filter}%"
                    conditions.append(
                        or_(
                            SMSNotificationORM.recipient_name.ilike(recipient_term),
                            SMSNotificationORM.recipient_phone.ilike(recipient_term)
                        )
                    )

                if conditions:
                    query = query.filter(and_(*conditions))

            return query.count()

    # Email Repository Methods
    def save_email(self, email: EmailNotification) -> EmailNotification:
        """Save Email notification to database."""
        with self._get_session() as session:
            if email.id:
                # Update existing
                db_email = session.query(EmailNotificationORM).filter(EmailNotificationORM.id == email.id).first()
                if db_email:
                    email_data = email.to_dict()
                    for key, value in email_data.items():
                        if key not in ['id', 'attachments'] and value is not None:
                            if key in ['sent_at', 'delivered_at', 'created_at', 'updated_at'] and isinstance(value,
                                                                                                             str):
                                value = datetime.fromisoformat(value)
                            setattr(db_email, key, value)
                    db_email.updated_at = datetime.now()

                    # Handle attachments
                    session.query(EmailAttachmentORM).filter(EmailAttachmentORM.email_id == email.id).delete()
                    for attachment in email.attachments:
                        db_attachment = EmailAttachmentORM(**attachment.to_dict())
                        db_attachment.email_id = email.id
                        session.add(db_attachment)

                    session.commit()
                    session.refresh(db_email)
                    return self._convert_email_orm_to_model(db_email)
            else:
                # Create new
                email_data = email.to_dict()
                del email_data['id']  # Remove id for new records
                # Convert datetime strings back to datetime objects
                for key in ['sent_at', 'delivered_at', 'created_at', 'updated_at']:
                    if email_data.get(key) and isinstance(email_data[key], str):
                        email_data[key] = datetime.fromisoformat(email_data[key])

                db_email = EmailNotificationORM(**email_data)
                session.add(db_email)
                session.flush()  # To get the ID

                # Add attachments
                for attachment in email.attachments:
                    attachment_data = attachment.to_dict()
                    del attachment_data['id']
                    db_attachment = EmailAttachmentORM(**attachment_data)
                    db_attachment.email_id = db_email.id
                    session.add(db_attachment)

                session.commit()
                session.refresh(db_email)
                return self._convert_email_orm_to_model(db_email)

    def get_email_by_id(self, email_id: int) -> Optional[EmailNotification]:
        """Get Email notification by ID."""
        with self._get_session() as session:
            db_email = session.query(EmailNotificationORM).filter(EmailNotificationORM.id == email_id).first()
            return self._convert_email_orm_to_model(db_email) if db_email else None

    def get_email_list(self, filter_criteria: NotificationFilter = None, limit: int = 100, offset: int = 0) -> List[
        EmailNotification]:
        """Get filtered list of Email notifications."""
        with self._get_session() as session:
            query = session.query(EmailNotificationORM)

            if filter_criteria and not filter_criteria.is_empty():
                conditions = []

                if filter_criteria.search_text:
                    search_term = f"%{filter_criteria.search_text}%"
                    conditions.append(
                        or_(
                            EmailNotificationORM.recipient_name.ilike(search_term),
                            EmailNotificationORM.recipient_email.ilike(search_term),
                            EmailNotificationORM.subject.ilike(search_term),
                            EmailNotificationORM.message.ilike(search_term)
                        )
                    )

                if filter_criteria.status:
                    conditions.append(EmailNotificationORM.status == filter_criteria.status)

                if filter_criteria.date_from:
                    conditions.append(EmailNotificationORM.created_at >= filter_criteria.date_from)

                if filter_criteria.date_to:
                    conditions.append(EmailNotificationORM.created_at <= filter_criteria.date_to)

                if filter_criteria.recipient_filter:
                    recipient_term = f"%{filter_criteria.recipient_filter}%"
                    conditions.append(
                        or_(
                            EmailNotificationORM.recipient_name.ilike(recipient_term),
                            EmailNotificationORM.recipient_email.ilike(recipient_term)
                        )
                    )

                if conditions:
                    query = query.filter(and_(*conditions))

            query = query.order_by(EmailNotificationORM.created_at.desc())
            db_email_list = query.offset(offset).limit(limit).all()

            return [self._convert_email_orm_to_model(db_email) for db_email in db_email_list]

    def get_email_count(self, filter_criteria: NotificationFilter = None) -> int:
        """Get count of Email notifications matching filter."""
        with self._get_session() as session:
            query = session.query(EmailNotificationORM)

            if filter_criteria and not filter_criteria.is_empty():
                conditions = []

                if filter_criteria.search_text:
                    search_term = f"%{filter_criteria.search_text}%"
                    conditions.append(
                        or_(
                            EmailNotificationORM.recipient_name.ilike(search_term),
                            EmailNotificationORM.recipient_email.ilike(search_term),
                            EmailNotificationORM.subject.ilike(search_term),
                            EmailNotificationORM.message.ilike(search_term)
                        )
                    )

                if filter_criteria.status:
                    conditions.append(EmailNotificationORM.status == filter_criteria.status)

                if filter_criteria.date_from:
                    conditions.append(EmailNotificationORM.created_at >= filter_criteria.date_from)

                if filter_criteria.date_to:
                    conditions.append(EmailNotificationORM.created_at <= filter_criteria.date_to)

                if filter_criteria.recipient_filter:
                    recipient_term = f"%{filter_criteria.recipient_filter}%"
                    conditions.append(
                        or_(
                            EmailNotificationORM.recipient_name.ilike(recipient_term),
                            EmailNotificationORM.recipient_email.ilike(recipient_term)
                        )
                    )

                if conditions:
                    query = query.filter(and_(*conditions))

            return query.count()

    # Helper methods
    def _convert_sms_orm_to_model(self, db_sms: SMSNotificationORM) -> SMSNotification:
        """Convert SMS ORM to model."""
        return SMSNotification(
            id=db_sms.id,
            recipient_name=db_sms.recipient_name,
            recipient_phone=db_sms.recipient_phone,
            message=db_sms.message,
            status=db_sms.status,
            sent_at=db_sms.sent_at,
            delivered_at=db_sms.delivered_at,
            provider_message_id=db_sms.provider_message_id,
            error_message=db_sms.error_message,
            created_at=db_sms.created_at,
            updated_at=db_sms.updated_at
        )

    def _convert_email_orm_to_model(self, db_email: EmailNotificationORM) -> EmailNotification:
        """Convert Email ORM to model."""
        attachments = [
            EmailAttachment(
                id=att.id,
                email_id=att.email_id,
                filename=att.filename,
                file_path=att.file_path,
                file_size=att.file_size,
                mime_type=att.mime_type
            )
            for att in db_email.attachments
        ]

        return EmailNotification(
            id=db_email.id,
            recipient_name=db_email.recipient_name,
            recipient_email=db_email.recipient_email,
            subject=db_email.subject,
            message=db_email.message,
            status=db_email.status,
            sent_at=db_email.sent_at,
            delivered_at=db_email.delivered_at,
            provider_message_id=db_email.provider_message_id,
            error_message=db_email.error_message,
            attachments=attachments,
            created_at=db_email.created_at,
            updated_at=db_email.updated_at
        )
