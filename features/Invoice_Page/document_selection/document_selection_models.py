# features/Invoice_Page/document_selection/document_selection_models.py

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple
import copy
import uuid


@dataclass
class DynamicPrice:
    """Represents a single selectable price option for a service."""
    id: int
    service_id: int
    name: str
    unit_price: int
    aliases: list[str] = field(default_factory=list)


@dataclass
class Service:
    """A unified application model representing any billable service."""
    id: int
    name: str
    type: str
    base_price: int
    dynamic_prices: list[DynamicPrice] = field(default_factory=list)
    default_page_count: int = 1
    aliases: list[str] = field(default_factory=list)

    @classmethod
    def to_dto(cls, service: "ServicesModel") -> "Service":
        return cls(
            id=service.id,
            name=service.name,
            type=service.type,
            base_price=service.base_price or 0,
            default_page_count=service.default_page_count,
            aliases=[alias.alias for alias in service.aliases],
            dynamic_prices=[fee.to_dto() for fee in service.dynamic_prices],
        )


@dataclass
class FixedPrice:
    """Represents a single fixed price item from the database."""
    id: int
    name: str
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
    dynamic_quantities: dict[str, int] = field(default_factory=dict)  # e.g., {'تعداد ترم': 8}
    remarks: str = ""

    dynamic_price_details: List[Tuple[str, int, int]] = field(default_factory=list)

    # Calculated prices from dialog
    translation_price: int = 0
    certified_copy_price: int = 0
    registration_price: int = 0
    judiciary_seal_price: int = 0
    foreign_affairs_seal_price: int = 0
    extra_copy_price: int = 0

    # The final, grand total for this item row
    total_price: int = 0

    unique_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def clone(self) -> 'PreviewItem':
        """Creates a deep copy of this PreviewItem."""
        new_item = copy.deepcopy(self)
        new_item.unique_id = str(uuid.uuid4())  # Ensure the clone is unique
        return new_item
