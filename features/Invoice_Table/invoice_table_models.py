# features/Invoice_Table/invoice_table_models.py

from dataclasses import dataclass
from typing import List, Optional
from shared.orm_models.invoices_models import InvoiceData, InvoiceItemData


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
