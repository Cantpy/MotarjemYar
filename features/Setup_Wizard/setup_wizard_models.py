# features/Setup_Wizard/setup_wizard_models.py

from dataclasses import dataclass
from enum import Enum, auto


class WizardStep(Enum):
    """Defines the possible steps in the setup wizard."""
    LICENSE = auto()
    TRANSLATION_OFFICE = auto()
    ADMIN_USER = auto()
    ADMIN_PROFILE = auto()
    COMPLETED = auto()


@dataclass
class LicenseDTO:
    """DTO for the license key provided by the user."""
    license_key: str


@dataclass
class TranslationOfficeDTO:
    """DTO for translation office data. Mirrors the ORM model."""
    name: str
    reg_no: str | None = None
    representative: str | None = None
    manager: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None


@dataclass
class AdminUserDTO:
    """DTO for the initial admin user's credentials and security info."""
    username: str
    password: str
    password_confirm: str
    security_question_1: str
    security_answer_1: str
    security_question_2: str
    security_answer_2: str


@dataclass
class AdminProfileDTO:
    user_id: int
    full_name: str
    national_id: str
    role_fa: str = "مدیر سیستم"
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    bio: str | None = None
