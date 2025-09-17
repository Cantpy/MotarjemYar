# shared/orm_models/workspace_models.py

from datetime import datetime
from typing import List

from sqlalchemy import (String, DateTime, Enum, ForeignKey, Boolean, Text, Integer)
from sqlalchemy.orm import relationship, Mapped, mapped_column, declarative_base
from sqlalchemy.sql import func
from shared.enums import ChatType, ParticipantRole


BaseWorkspace = declarative_base()


class ChatModel(BaseWorkspace):
    __tablename__ = 'chats'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=True)
    type: Mapped[ChatType] = mapped_column(Enum(ChatType), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # --- Relationships ---
    participants: Mapped[List["ChatParticipantModel"]] = relationship(back_populates="chat", cascade="all, delete-orphan")
    messages: Mapped[List["MessageModel"]] = relationship(back_populates="chat", cascade="all, delete-orphan")


class ChatParticipantModel(BaseWorkspace):
    __tablename__ = 'chat_participants'

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey('chats.id'), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)

    role: Mapped[ParticipantRole] = mapped_column(Enum(ParticipantRole), default=ParticipantRole.MEMBER)
    chat: Mapped["ChatModel"] = relationship(back_populates="participants")


class MessageModel(BaseWorkspace):
    __tablename__ = 'messages'

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    chat_id: Mapped[int] = mapped_column(ForeignKey('chats.id'), nullable=False)
    sender_id: Mapped[int] = mapped_column(Integer, nullable=False)

    chat: Mapped["ChatModel"] = relationship(back_populates="messages")
    attachments: Mapped[List["AttachmentModel"]] = relationship(back_populates="message", cascade="all, delete-orphan")
    read_receipts: Mapped[List["MessageReadStatusModel"]] = relationship(back_populates="message", cascade="all, delete-orphan")


# This table stores information about attached files
class AttachmentModel(BaseWorkspace):
    __tablename__ = 'attachments'

    id: Mapped[int] = mapped_column(primary_key=True)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=True)

    # --- Foreign Key ---
    message_id: Mapped[int] = mapped_column(ForeignKey('messages.id'), nullable=False)

    # --- Relationship ---
    message: Mapped["MessageModel"] = relationship(back_populates="attachments")


# This table tracks exactly who has read which message.
class MessageReadStatusModel(BaseWorkspace):
    __tablename__ = 'message_read_status'

    id: Mapped[int] = mapped_column(primary_key=True)
    read_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    message_id: Mapped[int] = mapped_column(ForeignKey('messages.id'), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)

    message: Mapped["MessageModel"] = relationship(back_populates="read_receipts")
