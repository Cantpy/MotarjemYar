# features/Workspace/workspace_repo.py

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

# You might need to adjust the import paths based on your project structure
from shared.orm_models.workspace_models import (ChatModel, ChatParticipantModel, MessageModel, MessageReadStatusModel,
                                                AttachmentModel)
from shared.orm_models.users_models import UsersModel
from shared.enums import ChatType, ParticipantRole
from features.Workspace.workspace_models import MessageDTO


class UserRepository:
    """A simple, read-only _repository for fetching user data."""

    def get_users_by_ids(self, session: Session, user_ids: List[int]) -> dict[int, UsersModel]:
        """
        Efficiently fetches multiple users by their IDs and returns them
        in a dictionary for quick lookup.
        """
        if not user_ids:
            return {}

        stmt = select(UsersModel).where(UsersModel.id.in_(user_ids))
        users = session.scalars(stmt).all()
        # Convert the list of users into a {user_id: User_object} dictionary
        return {user.id: user for user in users}


class ChatRepository:
    """
    Stateless _repository for all chat-related database operations.
    """

    def get_chats_for_user(self, session: Session, user_id: int) -> List[ChatModel]:
        """Fetches all chats that a specific user is a part of."""
        stmt = (
            select(ChatModel)
            .join(ChatModel.participants)
            .where(ChatParticipantModel.user_id == user_id)
        )
        return list(session.scalars(stmt).all())

    def get_messages_for_chat(self, session: Session, chat_id: int, limit: int = 50, offset: int = 0) -> List[MessageModel]:
        """Fetches a paginated list of messages for a given chat, ordered by creation time."""
        stmt = (
            select(MessageModel)
            .where(MessageModel.chat_id == chat_id)
            .order_by(MessageModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        # We fetch in descending order to get the latest, but reverse it for display
        results = session.scalars(stmt).all()
        return list(reversed(results))

    def get_participants_for_chat(self, session: Session, chat_id: int) -> List[ChatParticipantModel]:
        """Fetches all participants for a given chat, including their roles."""
        stmt = (
            select(ChatParticipantModel)
            .where(ChatParticipantModel.chat_id == chat_id)
        )
        return list(session.scalars(stmt).all())

    def get_participant_info(self, session: Session, user_id: int, chat_id: int) -> Optional[ChatParticipantModel]:
        """Gets a single participant's info (like their role) in a specific chat."""
        stmt = select(ChatParticipantModel).where(
            ChatParticipantModel.chat_id == chat_id,
            ChatParticipantModel.user_id == user_id
        )
        return session.scalars(stmt).one_or_none()

    def create_chat(self, session: Session, name: str, chat_type: ChatType,
                    initial_participants: List[ChatParticipantModel]) -> ChatModel:
        """Creates a new chat and adds its initial participants."""
        new_chat = ChatModel(
            name=name,
            type=chat_type,
            participants=initial_participants
        )
        session.add(new_chat)
        return new_chat

    def create_message(self, session: Session, chat_id: int, sender_id: int, content: str,
                       attachments: Optional[List[AttachmentModel]] = None) -> MessageModel:
        """Saves a new message to the database."""
        new_message = MessageModel(
            chat_id=chat_id,
            sender_id=sender_id,
            content=content,
            attachments=attachments or []
        )
        session.add(new_message)
        return new_message

    def mark_message_as_read(self, session: Session, message_id: int, user_id: int) -> Optional[MessageReadStatusModel]:
        """Marks a message as read by a user. Does nothing if already marked as read."""
        # First, check if a read receipt already exists
        stmt_exists = select(MessageReadStatusModel).where(
            MessageReadStatusModel.message_id == message_id,
            MessageReadStatusModel.user_id == user_id
        )
        existing_receipt = session.scalars(stmt_exists).first()

        if existing_receipt:
            return None  # Already read

        read_status = MessageReadStatusModel(
            message_id=message_id,
            user_id=user_id
        )
        session.add(read_status)
        return read_status

    def set_message_pin_status(self, session: Session, message_id: int, is_pinned: bool) -> Optional[MessageModel]:
        """Updates the is_pinned status of a message."""
        message_to_update = session.get(MessageModel, message_id)
        if message_to_update:
            message_to_update.is_pinned = is_pinned
        return message_to_update
