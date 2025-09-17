# shared/orm_models/workspace_models.py

import enum
from datetime import datetime
from typing import List

from sqlalchemy import (
    String,
    DateTime,
    Enum,
    ForeignKey,
    Boolean,
    Text
)
from sqlalchemy.orm import relationship, Mapped, mapped_column, declarative_base
from sqlalchemy.sql import func
from shared.orm_models.users_models import UsersModel


BaseWorkspace = declarative_base()


class ChatType(enum.Enum):
    ONE_ON_ONE = "one_on_one"
    GROUP = "group"
    CHANNEL = "channel"


class ParticipantRole(enum.Enum):
    MEMBER = "member"
    ADMIN = "admin"


# This is our first main table for the feature
class ChatModel(BaseWorkspace):
    __tablename__ = 'chats'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=True)
    type: Mapped[ChatType] = mapped_column(Enum(ChatType), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # --- Relationships ---
    # A chat has many participants (users)
    participants: Mapped[List["ChatParticipantModel"]] = relationship(back_populates="chat", cascade="all, delete-orphan")
    # A chat has many messages
    messages: Mapped[List["MessageModel"]] = relationship(back_populates="chat", cascade="all, delete-orphan")


class ChatParticipantModel(BaseWorkspace):
    __tablename__ = 'chat_participants'

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey('chats.id'), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    role: Mapped[ParticipantRole] = mapped_column(Enum(ParticipantRole), default=ParticipantRole.MEMBER)

    # --- Relationships ---
    # Connects back to the ChatModel model
    chat: Mapped["ChatModel"] = relationship(back_populates="participants")
    # Connects to your existing User model
    user: Mapped["UsersModel"] = relationship()


class MessageModel(BaseWorkspace):
    __tablename__ = 'messages'

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=True)  # The text of the message
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- Foreign Keys ---
    chat_id: Mapped[int] = mapped_column(ForeignKey('chats.id'), nullable=False)
    sender_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)

    # --- Relationships ---
    # Connects back to the ChatModel model
    chat: Mapped["ChatModel"] = relationship(back_populates="messages")
    # Connects to the User who sent the message
    sender: Mapped["UsersModel"] = relationship()

    # A message can have multiple attachments
    attachments: Mapped[List["AttachmentModel"]] = relationship(back_populates="message", cascade="all, delete-orphan")
    # A message has a read status for each user
    read_receipts: Mapped[List["MessageReadStatusModel"]] = relationship(back_populates="message",
                                                                         cascade="all, delete-orphan")


# This table stores information about attached files
class AttachmentModel(BaseWorkspace):
    __tablename__ = 'attachments'

    id: Mapped[int] = mapped_column(primary_key=True)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)  # Path to the file on the network share/server
    file_type: Mapped[str] = mapped_column(String(50), nullable=True)  # e.g., 'image/jpeg', 'application/pdf'

    # --- Foreign Key ---
    message_id: Mapped[int] = mapped_column(ForeignKey('messages.id'), nullable=False)

    # --- Relationship ---
    # Connects back to the MessageModel model
    message: Mapped["MessageModel"] = relationship(back_populates="attachments")


# This table tracks exactly who has read which message.
class MessageReadStatusModel(BaseWorkspace):
    __tablename__ = 'message_read_status'

    id: Mapped[int] = mapped_column(primary_key=True)
    read_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # --- Foreign Keys ---
    message_id: Mapped[int] = mapped_column(ForeignKey('messages.id'), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)

    # --- Relationships ---
    # Connects back to the MessageModel model
    message: Mapped["MessageModel"] = relationship(back_populates="read_receipts")
    # Connects to the User who read the message
    reader: Mapped["UsersModel"] = relationship()
