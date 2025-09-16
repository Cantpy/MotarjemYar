# features/Services/fixed_prices/fixed_prices_dto.py

from dataclasses import dataclass


@dataclass
class FixedPriceDTO:
    """Data Transfer Object for Fixed Price information."""
    id: int
    name: str
    price: int
    is_default: bool
    label_name: str | None = None
