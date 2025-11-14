# features/Admin_Panel/user_info/user_info_models.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class UsersData:
    id: int
    username: str
    password_hash: bytes
    role: str
    active: int
    display_name: str
    avatar_path: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    token_hash: Optional[str]
    expires_at: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    failed_login_attempts: int
    lockout_until_utc: Optional[datetime]
