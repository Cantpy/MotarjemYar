# features/Main_Window/main_window_models.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class UserProfileDTO:
    """
    Data Transfer Object holding user information for the main window UI.
    """
    id: int
    full_name: str
    role_fa: str
    avatar_path: Optional[str] = None
