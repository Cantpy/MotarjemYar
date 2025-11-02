# features/Admin_Panel/users_management/users_management_models.py

from dataclasses import dataclass
from datetime import date


@dataclass
class UserData:
    """
    A DTO for transferring user data between the UI, logic, and repo layers.
    It does not contain payroll information.
    """
    user_id: int | None = None
    username: str = ""
    password: str = ""  # Only used for creation or updating
    role: str = "clerk"
    is_active: bool = True
    start_date: date | None = None
    employee_id: str | None = None  # Link to the payroll system
    display_name: str = ""
