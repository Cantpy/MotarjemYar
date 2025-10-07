# features/Home_Page/home_page_models.py

import dataclasses
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import date
from shared.utils.persian_tools import to_persian_numbers


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
    most_repeated_document: Optional[Tuple[str, str]] = None
    most_repeated_document_month: Optional[Tuple[str, str]] = None

    def get_value_by_id(self, stat_id: str) -> str:
        """
        Helper method to get a stat value by its ID, now with Persian
        number conversion for all numeric values.
        """
        raw_values = {
            'total_customers': self.total_customers,
            'total_invoices': self.total_invoices,
            'today_invoices': self.today_invoices,
            'total_documents': self.total_documents,
            'available_documents': self.available_documents,
        }

        # Handle complex types first
        if stat_id == 'most_repeated_document':
            return self.most_repeated_document[0] if self.most_repeated_document else "نامشخص"
        if stat_id == 'most_repeated_document_month':
            return self.most_repeated_document_month[0] if self.most_repeated_document_month else "نامشخص"

        # Handle simple numeric types and convert them
        raw_value = raw_values.get(stat_id)
        if raw_value is not None:
            return to_persian_numbers(str(raw_value))

        return to_persian_numbers("0")  # Default value


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
