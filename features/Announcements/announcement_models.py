"""
Data orm_models for SMS and Email notifications.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class NotificationType(Enum):
    SMS = "sms"
    EMAIL = "email"


class NotificationStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"


@dataclass
class SMSNotification:
    """SMS notification data model."""
    id: Optional[int] = None
    recipient_name: str = ""
    recipient_phone: str = ""
    message: str = ""
    status: NotificationStatus = NotificationStatus.PENDING
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_dict(cls, data: dict) -> 'SMSNotification':
        """Create SMSNotification from dictionary."""
        return cls(
            id=data.get('id'),
            recipient_name=data.get('recipient_name', ''),
            recipient_phone=data.get('recipient_phone', ''),
            message=data.get('message', ''),
            status=NotificationStatus(data.get('status', 'pending')),
            sent_at=datetime.fromisoformat(data['sent_at']) if data.get('sent_at') else None,
            delivered_at=datetime.fromisoformat(data['delivered_at']) if data.get('delivered_at') else None,
            provider_message_id=data.get('provider_message_id'),
            error_message=data.get('error_message'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now()
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'recipient_name': self.recipient_name,
            'recipient_phone': self.recipient_phone,
            'message': self.message,
            'status': self.status.value,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'provider_message_id': self.provider_message_id,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class EmailAttachment:
    """Email attachment data model."""
    id: Optional[int] = None
    email_id: Optional[int] = None
    filename: str = ""
    file_path: str = ""
    file_size: int = 0
    mime_type: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> 'EmailAttachment':
        """Create EmailAttachment from dictionary."""
        return cls(
            id=data.get('id'),
            email_id=data.get('email_id'),
            filename=data.get('filename', ''),
            file_path=data.get('file_path', ''),
            file_size=data.get('file_size', 0),
            mime_type=data.get('mime_type', '')
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'email_id': self.email_id,
            'filename': self.filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type
        }


@dataclass
class EmailNotification:
    """Email notification data model."""
    id: Optional[int] = None
    recipient_name: str = ""
    recipient_email: str = ""
    subject: str = ""
    message: str = ""
    status: NotificationStatus = NotificationStatus.PENDING
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    attachments: List[EmailAttachment] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_dict(cls, data: dict, attachments: List[EmailAttachment] = None) -> 'EmailNotification':
        """Create EmailNotification from dictionary."""
        return cls(
            id=data.get('id'),
            recipient_name=data.get('recipient_name', ''),
            recipient_email=data.get('recipient_email', ''),
            subject=data.get('subject', ''),
            message=data.get('message', ''),
            status=NotificationStatus(data.get('status', 'pending')),
            sent_at=datetime.fromisoformat(data['sent_at']) if data.get('sent_at') else None,
            delivered_at=datetime.fromisoformat(data['delivered_at']) if data.get('delivered_at') else None,
            provider_message_id=data.get('provider_message_id'),
            error_message=data.get('error_message'),
            attachments=attachments or [],
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now()
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'recipient_name': self.recipient_name,
            'recipient_email': self.recipient_email,
            'subject': self.subject,
            'message': self.message,
            'status': self.status.value,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'provider_message_id': self.provider_message_id,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class NotificationFilter:
    """Filter criteria for notifications."""
    search_text: str = ""
    status: Optional[NotificationStatus] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    recipient_filter: str = ""

    def is_empty(self) -> bool:
        """Check if filter is empty."""
        return (
                not self.search_text and
                self.status is None and
                self.date_from is None and
                self.date_to is None and
                not self.recipient_filter
        )
