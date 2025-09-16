# features/Services/other_services/other_services_models.py

from dataclasses import dataclass


@dataclass
class OtherServiceDTO:
    """Data Transfer Object for Other Service information."""
    id: int
    name: str
    price: int
