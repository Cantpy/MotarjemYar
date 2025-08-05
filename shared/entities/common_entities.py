from dataclasses import dataclass
from typing import Optional
from datetime import date


@dataclass
class CustomerEntity:
    national_id: str
    name: str
    phone: str
    telegram_id: str
    email: str
    address: str
    passport_image: str


@dataclass
class ServicesEntity:
    """ServicesModel entity."""
    id: int
    name: str
    base_price: int
    dynamic_price_name_1: Optional[str] = None
    dynamic_price_1: Optional[int] = None
    dynamic_price_name_2: Optional[str] = None
    dynamic_price_2: Optional[int] = None


@dataclass
class InvoiceDocumentsEntity:
    """Invoice item entity."""
    id: int
    service_name: str
    quantity: int
    unit_price: str
    total_price: str
    officiality: bool
    judiciary_seal: bool
    foreign_affairs_seal: bool
    remarks: str


@dataclass
class InvoiceDetailsEntity:
    """Invoice entity."""
    id: int
    invoice_number: str
    name: str
    national_id: str
    phone: str
    issue_date: date
    delivery_date: date
    translator: str
    total_items: int
    total_amount: int
    total_translation_price: int
    advance_payment: int
    discount_amount: int
    force_majeure: int
    final_amount: int
    payment_status: int
    delivery_status: int
    total_official_docs_count: int
    total_unofficial_docs_count: int
    total_pages_count: int
    total_judiciary_count: int
    total_foreign_affairs_count: int
    total_additional_doc_count: int
    source_language: str
    target_language: str
    remarks: str
    username: str
    pdf_file_path: str
