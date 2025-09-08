# Home_Page/models.py
import dataclasses
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date


# --- DTOs for UI and Logic Communication ---
@dataclass
class TimeInfo:
    """Time information entity."""
    time_string: str
    date_string: str
    jalali_date: date


@dataclass
class DashboardStats:
    """Dashboard statistics entity."""
    total_customers: int
    total_invoices: int
    today_invoices: int
    total_documents: int
    available_documents: int
    most_repeated_document: Optional[str] = None
    most_repeated_document_month: Optional[str] = None

    def get_value_by_id(self, stat_id: str) -> str:
        # This is simple _view-helper logic, so it's acceptable here.
        value_map = {
            'total_customers': str(self.total_customers),
            'total_invoices': str(self.total_invoices),
            'today_invoices': str(self.today_invoices),
            'total_documents': str(self.total_documents),
            'available_documents': str(self.available_documents),
            'most_repeated_document': self.most_repeated_document or "نامشخص",
            'most_repeated_document_month': self.most_repeated_document_month or "نامشخص"
        }
        return value_map.get(stat_id, "0")


@dataclass
class DocumentStatistics:
    """Document statistics entity."""
    total_documents: int
    in_office_documents: int
    delivered_documents: int


@dataclass
class StatusChangeRequest:
    """Data class for status change requests."""
    invoice_number: int
    current_status: int
    target_status: int
    translator: Optional[str] = None


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
