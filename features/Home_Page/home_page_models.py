# features/Home_Page/home_page_models.py

import dataclasses
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date


@dataclass
class CustomerDTO:
    """Represents a customer's essential data."""
    name: str
    national_id: str
    phone: str


@dataclass
class InvoiceItemDTO:
    """Represents a line item in an invoice."""
    description: str
    quantity: int
    unit_price: int
    total_price: int


@dataclass
class InvoiceDTO:
    """Represents a complete invoice with nested objects."""
    invoice_number: str
    issue_date: date
    delivery_date: date

    username: str
    customer: CustomerDTO
    source_language: str
    target_language: str
    translator: str

    items: List[InvoiceItemDTO] = field(default_factory=list)

    total_amount: int = 0
    discount_amount: int = 0
    advance_payment: int = 0
    emergency_cost: int = 0
    final_amount: int = 0

    payment_status: Optional[int] = None
    delivery_status: Optional[int] = None
    remarks: str = ""
    pdf_file_path: Optional[str] = None

    @property
    def payable_amount(self) -> int:
        """Calculate payable amount based on components."""
        return (self.total_amount - self.discount_amount + self.emergency_cost) - self.advance_payment


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
        # This is simple _view-helper _logic, so it's acceptable here.
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
    invoice_number: str
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
