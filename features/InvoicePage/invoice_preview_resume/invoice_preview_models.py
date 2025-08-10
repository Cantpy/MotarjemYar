"""
Data models and entities for invoice preview functionality.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import date


@dataclass
class InvoiceSummary:
    """Summary data for invoice calculations."""
    total_official_docs_count: int = 0
    total_unofficial_docs_count: int = 0
    total_pages_count: int = 0
    total_judiciary_count: int = 0
    total_foreign_affairs_count: int = 0
    total_additional_doc_count: int = 0
    total_translation_price: int = 0


@dataclass
class InvoiceItem:
    """Individual invoice item data."""
    item_name: str
    item_qty: int
    item_price: int
    officiality: int = 0
    judiciary_seal: int = 0
    foreign_affairs_seal: int = 0
    remarks: Optional[str] = None


@dataclass
class InvoiceData:
    """Complete invoice data structure."""
    invoice_number: int
    customer_name: str
    national_id: str
    phone: str
    issue_date: date
    delivery_date: Optional[date]
    translator: str
    total_amount: int
    advance_payment: int = 0
    discount_amount: int = 0
    final_amount: int = 0
    source_language: Optional[str] = None
    target_language: Optional[str] = None
    remarks: Optional[str] = None
    username: str = ""
    pdf_file_path: Optional[str] = None
    items: List[InvoiceItem] = None
    summary: Optional[InvoiceSummary] = None

    def __post_init__(self):
        if self.items is None:
            self.items = []
        if self.summary is None:
            self.summary = InvoiceSummary()


@dataclass
class ScaleConfig:
    """UI scaling configuration for different display scales."""
    ui_module: str
    column_width: List[int]
    first_page_rows: int
    last_page_rows: int
    first_table_rows: int
    other_page_rows: int
    remarks_font: float
    scale_factor: float


@dataclass
class PaginationConfig:
    """Pagination configuration for invoice pages."""
    current_page: int = 1
    total_pages: int = 1
    total_rows: int = 0
    first_page_rows: int = 17
    last_page_rows: int = 16
    first_table_rows: int = 10
    other_page_rows: int = 26


@dataclass
class InvoiceStatistics:
    """Statistics about user's invoices."""
    total_invoices: int = 0
    draft_invoices: int = 0
    final_invoices: int = 0
    total_revenue: float = 0.0
    average_invoice_amount: float = 0.0
    total_advances: float = 0.0
    total_discounts: float = 0.0
    total_official_docs: int = 0
    total_unofficial_docs: int = 0
    total_pages: int = 0
    total_judiciary: int = 0
    total_foreign_affairs: int = 0
    total_additional_docs: int = 0
    total_translation_revenue: float = 0.0


@dataclass
class InvoiceExportData:
    """Data structure for invoice export operations."""
    invoice_number: str
    customer_name: str
    national_id: str
    phone: str
    issue_date: str
    delivery_date: str
    translator: str
    total_official_docs_count: int
    total_unofficial_docs_count: int
    total_pages_count: int
    total_judiciary_count: int
    total_foreign_affairs_count: int
    total_additional_doc_count: int
    total_translation_price: float
    total_amount: float
    advance_payment: float
    discount_amount: float
    final_amount: float
    language: str
    invoice_status: str
