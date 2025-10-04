from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# DTO for data persisted to the login_settings.json file
# ---------------------------------------------------------------------------


@dataclass
class RememberSettingsDTO:
    """
    Represents the data saved to disk for the 'Remember Me' feature.
    This is the data contract for the AuthFileRepository.
    """
    remember_me: bool         # Flag indicating if auto-login is enabled.
    username: str             # The username to attempt auto-login with.
    token: str                # The secret token to verify against the database.
    full_name: Optional[str]  # The user's full name, stored for a quick UI welcome message.


# ---------------------------------------------------------------------------
# Other related DTOs that belong in this file
# ---------------------------------------------------------------------------

@dataclass
class UserLoginDTO:
    """
    Represents the data coming from the login form (View -> Controller -> Logic).
    """
    username: str
    password: str
    remember_me: bool


@dataclass
class LoggedInUserDTO:
    """
    Represents the successfully authenticated user's session data.
    This is passed from the Logic layer up to the rest of the application.
    """
    username: str
    role: str
    full_name: Optional[str]
    role_fa: Optional[str]
    is_remembered: bool = False


@dataclass
class SessionDataDTO:
    """
    Represents the data for the currently active user session,
    persisted to a JSON file.
    """
    user_id: int
    username: str
    role: str
    full_name: Optional[str]
    role_fa: Optional[str]
    login_time: str
    log_id: int
