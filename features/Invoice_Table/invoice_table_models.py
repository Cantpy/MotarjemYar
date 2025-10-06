from dataclasses import dataclass
from typing import List, Optional


@dataclass
class InvoiceItemData:
    """Data class for invoice item information"""
    item_name: str
    item_qty: int
    item_price: int
    officiality: int
    judiciary_seal: int
    foreign_affairs_seal: int
    remarks: Optional[str] = None
    invoice_number: Optional[str] = None  # Added to match _repository usage

    def get_document_count(self) -> int:
        """Get document count for this item (used by _repository)"""
        return self.item_qty


@dataclass
class InvoiceData:
    """Data class for invoice information"""
    invoice_number: str  # Changed from int to str to match _repository
    name: str
    national_id: str  # Changed from int to str for better handling
    phone: str
    issue_date: str
    delivery_date: str
    translator: str
    total_items: Optional[int] = None
    total_amount: int = 0
    total_translation_price: int = 0
    advance_payment: int = 0
    discount_amount: int = 0
    emergency_cost: int = 0
    final_amount: int = 0
    payment_status: int = 0
    delivery_status: int = 0
    total_official_docs_count: int = 0
    total_unofficial_docs_count: int = 0
    total_pages_count: int = 0
    total_judiciary_count: int = 0
    total_foreign_affairs_count: int = 0
    total_additional_doc_count: int = 0
    source_language: Optional[str] = None
    target_language: Optional[str] = None
    remarks: Optional[str] = None
    username: Optional[str] = None
    pdf_file_path: Optional[str] = None
    items: List[InvoiceItemData] = None
    id: Optional[int] = None  # Added database ID field

    def __post_init__(self):
        """Initialize items list if None"""
        if self.items is None:
            self.items = []


@dataclass
class InvoiceSummary:
    """Data class for invoice summary statistics"""
    total_count: int
    total_amount: float
    translator_stats: List[tuple]  # List of (translator_name, count) tuples


@dataclass
class DocumentCount:
    """Data class for document count information"""
    invoice_number: str
    count: int


@dataclass
class UserData:
    """Data class for user information"""
    username: str
    role: str
    active: bool = True
    full_name: Optional[str] = None
    id: Optional[int] = None


@dataclass
class UserProfileData:
    """Data class for user profile information"""
    username: str
    full_name: str
    id: Optional[int] = None


# Export data structures for _repository methods
@dataclass
class ExportInvoiceData:
    """Simplified data class for invoice export"""
    invoice_number: str
    name: str
    national_id: str
    phone: str
    issue_date: str
    delivery_date: str
    translator: str
    total_amount: int


class InvoiceFilter:
    """Class for managing invoice filtering criteria"""

    def __init__(self):
        self.search_text: str = ""
        self.visible_columns: List[bool] = [True] * 10

    def set_search_text(self, text: str):
        """Set search text filter"""
        self.search_text = text.lower()

    def set_column_visibility(self, column_index: int, visible: bool):
        """Set column visibility"""
        if 0 <= column_index < len(self.visible_columns):
            self.visible_columns[column_index] = visible

    def matches_search(self, invoice: InvoiceData) -> bool:
        """Check if invoice matches search criteria"""
        if not self.search_text:
            return True

        searchable_fields = [
            invoice.invoice_number,
            invoice.name,
            invoice.national_id,
            invoice.phone,
            invoice.translator
        ]

        return any(self.search_text in str(field).lower() for field in searchable_fields)


class ColumnSettings:
    """Class for managing column visibility settings"""

    COLUMN_NAMES = [
        "شماره فاکتور", "نام", "کد ملی", "شماره تماس", "تاریخ صدور",
        "تاریخ تحویل", "مترجم", "تعداد اسناد", "هزیته فاکتور", "مشاهده فاکتور"
    ]

    def __init__(self):
        self.visible_columns = [True] * len(self.COLUMN_NAMES)

    def get_column_name(self, index: int) -> str:
        """Get column name by index"""
        if 0 <= index < len(self.COLUMN_NAMES):
            return self.COLUMN_NAMES[index]
        return ""

    def set_column_visible(self, index: int, visible: bool):
        """Set column visibility"""
        if 0 <= index < len(self.visible_columns):
            self.visible_columns[index] = visible

    def is_column_visible(self, index: int) -> bool:
        """Check if column is visible"""
        if 0 <= index < len(self.visible_columns):
            return self.visible_columns[index]
        return False
