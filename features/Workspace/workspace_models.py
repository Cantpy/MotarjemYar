# features/Workspace/workspace_models.py file

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from shared.enums import ChatType


@dataclass(frozen=True)
class UserDTO:
    """A simplified User representation for the UI."""
    id: int
    name: str


@dataclass(frozen=True)
class AttachmentDTO:
    """Represents a file attached to a message."""
    id: int
    file_path: str
    file_type: str


@dataclass(frozen=True)
class MessageReadReceiptDTO:
    """Represents who has read a message and when."""
    user: UserDTO
    read_at: datetime


@dataclass(frozen=True)
class MessageDTO:
    """The primary DTO for displaying a single message in the UI."""
    id: int
    content: str
    sender: UserDTO
    created_at: datetime
    is_pinned: bool
    attachments: List[AttachmentDTO] = field(default_factory=list)
    read_receipts: List[MessageReadReceiptDTO] = field(default_factory=list)


@dataclass(frozen=True)
class ChatDTO:
    """Represents a single chat in the chat list panel."""
    id: int
    name: str  # The name to be displayed in the UI
    type: ChatType
    unread_count: int = 0
    last_message: Optional[MessageDTO] = None
