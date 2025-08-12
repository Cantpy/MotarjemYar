# models.py
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Companion:
    """Data class for a companion."""
    id: Optional[int] = None
    name: str = ""
    national_id: int = 0


@dataclass
class Customer:
    """Data class for a customer."""
    national_id: int = 0
    name: str = ""
    phone: str = ""
    telegram_id: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    passport_image: Optional[str] = None
    companions: List[Companion] = field(default_factory=list)
