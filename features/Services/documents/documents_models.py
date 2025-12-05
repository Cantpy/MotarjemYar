# features/Services/documents/documents_models.py

from dataclasses import dataclass, field, asdict


@dataclass
class ServiceDynamicFeeDTO:
    """Data Transfer Object for dynamic fees attached to a service."""
    id: int
    service_id: int
    name: str
    unit_price: int
    aliases: list[str] = field(default_factory=list)


@dataclass
class ServicesDTO:
    """Data Transfer Object for Service information."""
    id: int
    name: str
    base_price: int
    default_page_count: int
    aliases: list[str] = field(default_factory=list)
    dynamic_prices: list[ServiceDynamicFeeDTO] = field(default_factory=list)


@dataclass
class NormalizedDynamicPriceDTO:
    """DTO for a cleaned, validated dynamic price ready for DB insertion."""
    name: str
    unit_price: int
    aliases: list[dict] = field(default_factory=list)  # Format: [{'alias': 'name'}]


@dataclass
class NormalizedServiceDTO:
    """DTO for a cleaned, validated Service ready for DB insertion."""
    name: str
    base_price: int
    default_page_count: int
    aliases: list[dict] = field(default_factory=list) # Format: [{'alias': 'name'}]
    dynamic_prices: list[NormalizedDynamicPriceDTO] = field(default_factory=list)

    def to_dict(self):
        """Helper to convert back to dictionary for the Repository layer."""
        return asdict(self)