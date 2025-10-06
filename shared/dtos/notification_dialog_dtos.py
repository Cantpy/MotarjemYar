# shared/dtos/notification_dialog_dtos.py

import dataclasses
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SmsRequestDTO:
    """Data required to send an SMS."""
    recipient_phone: str
    message: str


@dataclass
class EmailRequestDTO:
    """Data required to send an Email."""
    recipient_name: str
    recipient_email: str
    message: str
    attachments: List[str] = dataclasses.field(default_factory=list)


@dataclass
class NotificationDataDTO:
    """
    Contains all the necessary data to show and operate
    the notification dialog for a ready invoice.
    """
    invoice_number: str
    customer_name: str
    customer_national_id: str
    customer_phone: Optional[str]
    customer_email: Optional[str]
