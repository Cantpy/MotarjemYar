# models.py

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date


@dataclass
class TranslationOffice:
    """Represents the contact and identity information for the translation office."""
    name: str
    reg_no: str
    representative: str
    address: str
    phone: str
    email: str
    socials: str
    logo_path: str


@dataclass
class Customer:
    """Represents the customer's information."""
    name: str
    national_id: str
    phone: str
    address: str


@dataclass
class InvoiceItem:
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
    issue_date: date
    delivery_date: date
    username: str
    customer: Customer
    office: TranslationOffice
    source_language: str
    target_language: str
    items: List[InvoiceItem] = field(default_factory=list)
    total_amount: float = 0.0
    discount_amount: float = 0.0
    advance_payment: float = 0.0
    emergency_cost: float = 0.0
    remarks: str = ""

    @property
    def payable_amount(self) -> float:
        """Calculates the final amount to be paid, now including emergency cost."""
        return (self.total_amount - self.discount_amount + self.emergency_cost) - self.advance_payment
