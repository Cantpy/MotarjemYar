# shared/dtos/customers_dto.py

from dataclasses import dataclass


@dataclass
class CustomerDTO:
    """Data Transfer Object for Customer information."""
    national_id: str
    name: str
    phone: str
    telegram_id: str | None = None
    email: str | None = None
    address: str | None = None
    passport_image: str | None = None


@dataclass
class CompanionDTO:
    """Data Transfer Object for Companion information."""
    id: int | None = None
    name: str = ""
    national_id: str = ""
    customer_national_id: str = ""
