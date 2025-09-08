# orm_models.py
from dataclasses import dataclass, field


@dataclass
class Companion:
    """Data class for a companion."""
    id: int | None = None
    name: str = ""
    national_id: str = ""


@dataclass
class Customer:
    """Data class for a customer."""
    national_id: str = ""
    name: str = ""
    phone: str = ""
    telegram_id: str | None = None
    email: str | None = None
    address: str | None = None
    passport_image: str | None = None
    companions: list[Companion] = field(default_factory=list)
