# features/Admin_Panel/users_management/users_management_models.py

from dataclasses import dataclass
from datetime import date


@dataclass
class UserData:
    """
    A DTO for transferring user data between the UI, logic, and repo layers.
    It is self-contained within the users' domain.
    """
    user_id: int | None = None
    username: str = ""
    password: str = ""
    role: str = "clerk"
    is_active: bool = True
    start_date: date | None = None
    display_name: str = ""
