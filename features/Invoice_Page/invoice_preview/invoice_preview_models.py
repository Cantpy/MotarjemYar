# features/Invoice_Page/invoice_preview/invoice_preview_models.py

from dataclasses import dataclass, field
from typing import List
from datetime import datetime


@dataclass
class PreviewOfficeInfo:
    """Represents the contact and identity information for the translation office."""
    name: str
    reg_no: str
    representative: str
    address: str
    phone: str
    email: str
    website: str
    whatsapp: str
    telegram: str
    logo: bytes | None = None


@dataclass
class Customer:
    """Represents the customer's information."""
    name: str
    national_id: str
    phone: str
    address: str = ""


@dataclass
class PreviewItem:
    """Represents a single item line in an invoice."""
    name: str
    type: str
    quantity: int
    judiciary_seal: str
    foreign_affairs_seal: str
    total_price: float


@dataclass
class Invoice:
    """Represents the entire invoice data for a single transaction."""
    invoice_number: str

    issue_date: datetime
    delivery_date: datetime

    username: str
    customer: Customer
    office: PreviewOfficeInfo
    source_language: str
    target_language: str
    items: List[PreviewItem] = field(default_factory=list)

    total_translation_price: int = 0
    total_confirmation_price: int = 0
    total_office_price: int = 0
    total_certified_copy_price: int = 0
    total_additional_price: int = 0
    total_amount: int = 0
    discount_amount: int = 0
    advance_payment: int = 0
    emergency_cost: int = 0

    remarks: str = ""

    @property
    def payable_amount(self) -> int:
        """Calculates the final amount to be paid."""
        return (self.total_amount - self.discount_amount + self.emergency_cost) - self.advance_payment
