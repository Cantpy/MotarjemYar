# Login/login_window_models.py

from dataclasses import dataclass
from typing import Optional


# Data Transfer Objects (DTOs)
@dataclass
class UserLoginDTO:
    username: str
    password: str
    remember_me: bool


@dataclass
class LoggedInUserDTO:
    username: str
    role: str
    role_fa: Optional[str]
    full_name: str
    is_remembered: bool


@dataclass
class RememberSettingsDTO:
    remember_me: bool
    username: str
    token: str
    full_name: str
