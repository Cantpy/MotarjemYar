# features/Services/documents/documents_models.py

from dataclasses import dataclass, field


@dataclass
class ServiceDynamicFeeDTO:
    """Data Transfer Object for dynamic fees attached to a service."""
    id: int
    service_id: int
    name: str
    unit_price: int


@dataclass
class ServicesDTO:
    """Data Transfer Object for Service information."""
    id: int
    name: str
    base_price: int
    dynamic_fees: list[ServiceDynamicFeeDTO] = field(default_factory=list)
