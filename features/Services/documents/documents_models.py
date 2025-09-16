# features/Services/documents/documents_models.py

from dataclasses import dataclass, field


@dataclass
class ServicesDTO:
    """Data Transfer Object for Service information."""
    id: int
    name: str
    base_price: int | None
    dynamic_price_name_1: str | None
    dynamic_price_1: int | None
    dynamic_price_name_2: str | None
    dynamic_price_2: int | None


@dataclass
class ImportResult:
    """Data Transfer Object for the results of an import operation."""
    source: str  # e.g., "Excel" or "Database"
    success_count: int = 0
    failed_count: int = 0
    added_services_names: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
