# document_selection/models.py
from dataclasses import dataclass, field
import copy
from typing import List, Dict


@dataclass
class DynamicPrice:
    """Represents a single selectable price option for a service."""
    name: str
    price: int


@dataclass
class Service:
    """A unified application model representing any billable service."""
    name: str
    type: str
    base_price: int
    dynamic_prices: List[DynamicPrice] = field(default_factory=list)


@dataclass
class FixedPrice:
    """Represents a single fixed price item from the database."""
    name: str
    label_name: str
    price: int


@dataclass
class InvoiceItem:
    """Represents a fully configured and calculated item for the invoice."""
    service: Service  # Keep the original service for reference

    # User inputs from dialog
    quantity: int = 1
    page_count: int = 0
    extra_copies: int = 0
    is_official: bool = False
    has_judiciary_seal: bool = False
    has_foreign_affairs_seal: bool = False
    dynamic_quantities: Dict[str, int] = field(default_factory=dict)  # e.g., {'تعداد ترم': 8}
    remarks: str = ""

    # Calculated prices from dialog
    translation_price: int = 0
    certified_copy_price: int = 0
    registration_price: int = 0
    judiciary_seal_price: int = 0
    foreign_affairs_seal_price: int = 0
    extra_copy_price: int = 0

    # The final, grand total for this item row
    total_price: int = 0

    def clone(self) -> 'InvoiceItem':
        """Creates a deep copy of this InvoiceItem."""
        return copy.deepcopy(self)
