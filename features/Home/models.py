"""
Domain models for the home page functionality.
These represent the business entities and data structures.
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import date


@dataclass
class Settings:
    """Settings storage entity for homepage."""
    row_count: int
    threshold_days: int
    orange_threshold_days: int
    red_threshold_days: int
    total_cards_number: int
    stat_cards: Optional[List[tuple]] = None


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


@dataclass
class TimeInfo:
    """Time information entity."""
    time_string: str
    date_string: str
    jalali_date: date


@dataclass
class InvoiceTableRow:
    """Invoice table row data."""
    invoice_number: str
    name: str
    phone: str
    delivery_date: str
    translator: str
    pdf_file_path: str
    delivery_status: int
    delivery_date_obj: date
    row_color: str  # Color indicator for urgency


@dataclass
class DocumentStatistics:
    """Document statistics entity."""
    total_documents: int
    in_office_documents: int
    delivered_documents: int
    most_repeated_document: str = None
    most_repeated_document_month: str = None


@dataclass
class StatusChangeRequest:
    """Data class for status change requests."""
    invoice_number: int
    current_status: int
    target_status: int
    translator: Optional[str] = None


class DeliveryStatus:
    """Constants for delivery status values."""
    ISSUED = 0          # فاکتور صادر شده، هنوز برای ترجمه ارسال نشده
    ASSIGNED = 1        # مترجم تعیین شده
    TRANSLATED = 2      # اسناد ترجمه شده، آماده امضا و مهر
    READY = 3          # کاملاً آماده، منتظر دریافت توسط مشتری
    COLLECTED = 4      # توسط مشتری دریافت شده

    @classmethod
    def get_status_text(cls, status: int) -> str:
        """Get Persian text for status."""
        status_map = {
            cls.ISSUED: "صادر شده",
            cls.ASSIGNED: "مترجم تعیین شده",
            cls.TRANSLATED: "ترجمه شده",
            cls.READY: "آماده تحویل",
            cls.COLLECTED: "تحویل داده شده"
        }
        return status_map.get(status, "نامشخص")

    @classmethod
    def get_next_step_text(cls, current_status: int) -> str:
        """Get text for the next step button."""
        step_map = {
            cls.ISSUED: "تعیین مترجم",
            cls.ASSIGNED: "تأیید ترجمه",
            cls.TRANSLATED: "آماده تحویل",
            cls.READY: "تحویل به مشتری"
        }
        return step_map.get(current_status, "")

    @classmethod
    def can_advance(cls, current_status: int) -> bool:
        """Check if status can be advanced."""
        return current_status < cls.COLLECTED
