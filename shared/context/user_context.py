from dataclasses import dataclass


@dataclass
class UserContext:
    username: str
    full_name: str
    role: str
    role_fa: str
    avatar: str
