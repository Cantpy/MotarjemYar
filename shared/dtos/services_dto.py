# shared/dtos/services_dto.py

from dataclasses import dataclass


@dataclass
class ServiceDTO:
    """Data Transfer Object for Service information."""
    id: int
    name: str
    base_price: int | None
    dynamic_price_name_1: str | None
    dynamic_price_1: int | None
    dynamic_price_name_2: str | None
    dynamic_price_2: int | None


@dataclass
class FixedPriceDTO:
    """Data Transfer Object for Fixed Price information."""
    id: int
    name: str
    price: int


@dataclass
class OtherServiceDTO:
    """Data Transfer Object for Other Service information."""
    id: int
    name: str
    price: int
