# shared/dtos/users_dtos.py

from dataclasses import dataclass


@dataclass
class UsersDTO:
    """Data Transfer Object for UsersModel"""
    id: int
    username: str
    role: str
    active: int
    start_date: str | None
    end_date: str | None
    created_at: str | None
    updated_at: str | None


@dataclass
class UserProfileDTO:
    """Data Transfer Object for UserProfileModel"""
    id: int
    user_id: int
    full_name: str
    role_fa: str
    date_of_birth: str | None
    email: str | None
    phone: str | None
    national_id: str | None
    address: str | None
    bio: str | None
    avatar_path: str | None
    created_at: str | None
    updated_at: str | None


@dataclass
class LoginLogsDTO:
    """Data Transfer Object for LoginLogsModel"""
    id: int
    user_id: int
    login_time: str | None
    logout_time: str | None
    time_on_app: int | None
    status: str | None
    ip_address: str | None
    user_agent: str | None


@dataclass
class TranslationOfficeDataDTO:
    """Data Transfer Object for TranslationOfficeDataModel"""
    id: int
    name: str
    reg_no: str | None
    representative: str | None
    manager: str | None
    address: str | None
    phone: str | None
    email: str | None
    website: str | None
    whatsapp: str | None
    instagram: str | None
    telegram: str | None
    other_media: str | None
    open_hours: str | None
    map_url: str | None
    created_at: str | None
    updated_at: str | None
