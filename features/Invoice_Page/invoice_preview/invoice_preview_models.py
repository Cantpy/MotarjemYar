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
    address: str


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
    total_amount: float = 0.0
    discount_amount: float = 0.0
    advance_payment: float = 0.0
    emergency_cost: float = 0.0
    remarks: str = ""

    @property
    def payable_amount(self) -> float:
        """Calculates the final amount to be paid, now including emergency cost."""
        return (self.total_amount - self.discount_amount + self.emergency_cost) - self.advance_payment
