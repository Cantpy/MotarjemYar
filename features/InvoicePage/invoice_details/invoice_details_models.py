from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any
from enum import Enum

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any
from enum import Enum


class Language(Enum):
    """Supported languages for translation."""
    FARSI = "فارسی"
    ENGLISH = "انگلیسی"
    ARABIC = "عربی"
    GERMAN = "آلمانی"
    FRENCH = "فرانسوی"
    SPANISH = "اسپانیولی"
    ITALIAN = "ایتالیایی"
    RUSSIAN = "روسی"
    CHINESE = "چینی"
    JAPANESE = "ژاپنی"
    KOREAN = "کره‌ای"
    TURKISH = "ترکی استانبولی"
    AZERBAIJANI = "آذربایجانی"
    URDU = "اردو"
    ARMENIAN = "ارمنی"
    ROMANIAN = "رومانیایی"
    SERBIAN = "صربی"
    KURDISH = "کردی"


@dataclass
class CustomerInfo:
    """Customer information data class."""
    name: str = ""
    phone: str = ""
    national_id: str = ""
    email: str = ""
    address: str = ""
    total_companions: int = 0


@dataclass
class TranslationOfficeInfo:
    """Translation office information data class."""
    name: str = ""
    registration_number: str = ""
    representative: str = ""
    manager: str = ""
    address: str = ""
    phone: str = ""
    website: str = ""
    whatsapp: str = ""
    instagram: str = ""
    telegram: str = ""
    other_media: str = ""
    open_hours: str = ""
    map_url: str = ""


@dataclass
class FinancialData:
    """Financial data for invoice."""
    translation_cost: int = 0
    confirmation_cost: int = 0
    office_affairs_cost: int = 0
    copy_certification_cost: int = 0
    emergency_cost: int = 0
    is_emergency: bool = False
    discount_amount: int = 0
    advance_payment: int = 0

    @property
    def subtotal(self) -> int:
        """Calculate subtotal before discount and advance payment."""
        return (self.translation_cost + self.confirmation_cost +
                self.office_affairs_cost + self.copy_certification_cost +
                self.emergency_cost)

    @property
    def final_amount(self) -> int:
        """Calculate final amount after discount and advance payment."""
        return max(0, self.subtotal - self.discount_amount - self.advance_payment)


@dataclass
class DocumentCounts:
    """Document counts for invoice."""
    total_official_docs: int = 0
    total_unofficial_docs: int = 0
    total_pages: int = 0
    total_judiciary: int = 0
    total_foreign_affairs: int = 0
    total_additional_docs: int = 0

    @property
    def total_documents(self) -> int:
        """Calculate total number of documents."""
        return (self.total_official_docs + self.total_unofficial_docs +
                self.total_judiciary + self.total_foreign_affairs +
                self.total_additional_docs)


@dataclass
class UserInfo:
    """Current user information."""
    username: str = ""
    role: str = ""
    full_name: str = ""


@dataclass
class InvoiceValidationResult:
    """Invoice validation result."""
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class InvoiceData:
    """Complete invoice data."""
    receipt_number: str
    username: str
    receive_date: datetime
    delivery_date: Optional[date] = None
    source_language: Language = Language.FARSI
    target_language: Language = Language.ENGLISH
    financial: Optional[FinancialData] = None
    office_info: Optional[TranslationOfficeInfo] = None
    customer_info: Optional[CustomerInfo] = None
    document_counts: Optional[DocumentCounts] = None
    remarks: str = ""

    def __post_init__(self):
        """Initialize optional fields if not provided."""
        if self.financial is None:
            self.financial = FinancialData()
        if self.document_counts is None:
            self.document_counts = DocumentCounts()


@dataclass
class InvoiceDetailsRequest:
    """Request object for invoice details operations."""
    current_user: str
    document_count: Optional[int] = None
    customer_info: Optional[CustomerInfo] = None


@dataclass
class InvoiceDetailsResponse:
    """Response object for invoice details operations."""
    success: bool
    message: str
    invoice_data: Optional[InvoiceData] = None
    next_receipt_number: Optional[str] = None
    office_info: Optional[TranslationOfficeInfo] = None
    user_info: Optional[UserInfo] = None
    errors: Optional[list] = None
    

# @dataclass
# class InvoiceData:
#     """Complete invoice data structure."""
#     # Basic invoice information
#     receipt_number: str = ""
#     invoice_number: int = 0
#     receive_date: datetime = field(default_factory=datetime.now)
#     delivery_date: Optional[date] = None
#     username: str = ""
#
#     # Language information
#     source_language: Language = Language.FARSI
#     target_language: Language = Language.ENGLISH
#
#     # Financial data
#     financial: FinancialData = field(default_factory=FinancialData)
#
#     # Document counts
#     document_counts: DocumentCounts = field(default_factory=DocumentCounts)
#
#     # Related information
#     customer_info: CustomerInfo = field(default_factory=CustomerInfo)
#     office_info: TranslationOfficeInfo = field(default_factory=TranslationOfficeInfo)
#     user_info: UserInfo = field(default_factory=UserInfo)
#
#     # Additional information
#     remarks: str = ""
#     translator: str = ""
#
#     # Status information
#     payment_status: int = 0  # 0: unpaid, 1: paid
#     delivery_status: int = 0  # 0: pending, 1: in_progress, 2: ready, 3: delivered, 4: cancelled
#
#     def to_dict(self) -> Dict[str, Any]:
#         """Convert to dictionary for database operations."""
#         return {
#             'invoice_number': self.invoice_number,
#             'name': self.customer_info.name,
#             'national_id': self.customer_info.national_id,
#             'phone': self.customer_info.phone,
#             'issue_date': self.receive_date.date() if isinstance(self.receive_date, datetime) else self.receive_date,
#             'delivery_date': self.delivery_date,
#             'translator': self.translator,
#             'total_items': self.document_counts.total_documents,
#             'total_amount': int(self.financial.final_amount + self.financial.advance_payment),
#             'total_translation_price': int(self.financial.translation_cost),
#             'advance_payment': int(self.financial.advance_payment),
#             'discount_amount': int(self.financial.discount_amount),
#             'force_majeure': int(self.financial.emergency_cost),
#             'final_amount': int(self.financial.final_amount),
#             'payment_status': self.payment_status,
#             'delivery_status': self.delivery_status,
#             'total_official_docs_count': self.document_counts.total_official_docs,
#             'total_unofficial_docs_count': self.document_counts.total_unofficial_docs,
#             'total_pages_count': self.document_counts.total_pages,
#             'total_judiciary_count': self.document_counts.total_judiciary,
#             'total_foreign_affairs_count': self.document_counts.total_foreign_affairs,
#             'total_additional_doc_count': self.document_counts.total_additional_docs,
#             'source_language': self.source_language.value,
#             'target_language': self.target_language.value,
#             'remarks': self.remarks,
#             'username': self.username,
#         }
