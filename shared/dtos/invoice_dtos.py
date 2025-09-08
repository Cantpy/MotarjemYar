# shared/dtos/invoice_dtos.py

from dataclasses import dataclass


@dataclass
class InvoiceItemsDTO:
    """DTO for individual invoice items."""
    service: int
    quantity: int
    page_count: int
    additional_issues: int
    is_official: int
    has_judiciary_seal: int
    has_foreign_affairs_seal: int
    dynamic_price_1: int
    dynamic_price_2: int
    dynamic_price_amount_1: int
    dynamic_price_amount_2: int
    remarks: str | None
    translation_price: int
    certified_copy_price: int
    registration_price: int
    judiciary_seal_price: int
    foreign_affairs_seal_price: int
    additional_issues_price: int
    total_price: int


@dataclass
class IssuedInvoiceDTO:
    """DTO for issued invoices."""
    invoice_number: int
    name: str
    national_id: int
    phone: str
    issue_date: str
    delivery_date: str
    translator: str
    total_items: int | None
    total_amount: int
    total_translation_price: int
    advance_payment: int
    discount_amount: int
    force_majeure: int
    final_amount: int
    payment_status: int
    delivery_status: int
    username: str | None
    pdf_file_path: str | None
