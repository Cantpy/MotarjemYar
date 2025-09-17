# features/Workspace/workspace_logic.py

from typing import List, Optional
from contextlib import contextmanager

from features.Workspace.workspace_repo import ChatRepository, UserRepository
from shared.session_provider import SessionProvider
from features.Workspace.workspace_models import ChatDTO, MessageDTO, UserDTO, AttachmentDTO, MessageReadReceiptDTO
from shared.orm_models.workspace_models import (MessageModel, ChatModel, ChatParticipantModel, ChatType,
                                                ParticipantRole)
from shared.orm_models.users_models import UsersModel
from server.client import ChatClient


class ChatLogic:
    def __init__(self, user_repository: UserRepository,
                 chat_repository: ChatRepository,
                 session_provider: SessionProvider,
                 client: ChatClient):
        self._user_repo = user_repository
        self._chat_repo = chat_repository
        self._session_provider = session_provider
        self._client = client

    # --- Data Transformation (Mapping) Methods ---

    def _get_user_details_map(self, user_ids: List[int]) -> dict[int, UserDTO]:
        """Fetches user data from the users DB and maps it to DTOs."""
        if not user_ids:
            return {}
        with self._session_provider.users() as user_session:  # Use the 'users' DB
            users_map = self._user_repo.get_users_by_ids(user_session, user_ids)
            return {
                user_id: UserDTO(id=user.id, name=user.username)
                for user_id, user in users_map.items()
            }

    def _map_message_to_dto(self, message: MessageModel) -> MessageDTO:
        """Converts a Message SQLAlchemy model to a MessageDTO."""
        sender_dto = UserDTO(id=message.sender.id, name=message.sender.username)

        attachment_dtos = [
            AttachmentDTO(id=att.id, file_path=att.file_path, file_type=att.file_type)
            for att in message.attachments
        ]

        read_receipt_dtos = [
            MessageReadReceiptDTO(
                user=UserDTO(id=receipt.reader.id, name=receipt.reader.username),
                read_at=receipt.read_at
            )
            for receipt in message.read_receipts
        ]

        return MessageDTO(
            id=message.id,
            content=message.content,
            sender=sender_dto,
            created_at=message.created_at,
            is_pinned=message.is_pinned,
            attachments=attachment_dtos,
            read_receipts=read_receipt_dtos
        )

    # --- Public Business Logic Methods ---

    def get_chats_for_user(self, user_id: int) -> List[ChatDTO]:
        with self._session_provider.workspace() as chat_session:
            chats = self._chat_repo.get_chats_for_user(chat_session, user_id)

            # 1. Collect all participant user IDs from all chats
            all_participant_ids = set()
            for chat in chats:
                for p in chat.participants:
                    all_participant_ids.add(p.user_id)

            # 2. Fetch all user details in a single query
            user_details_map = self._get_user_details_map(list(all_participant_ids))

            # 3. Build the DTOs
            chat_dtos = []
            for chat in chats:
                display_name = chat.name
                if chat.type == ChatType.ONE_ON_ONE:
                    other_participant = next((p for p in chat.participants if p.user_id != user_id), None)
                    if other_participant and other_participant.user_id in user_details_map:
                        display_name = user_details_map[other_participant.user_id].name

                chat_dtos.append(ChatDTO(id=chat.id, name=display_name, type=chat.type))
            return chat_dtos

    def get_chat_history(self, chat_id: int) -> List[MessageDTO]:
        with self._session_provider.workspace as chat_session:
            messages = self._chat_repo.get_messages_for_chat(chat_session, chat_id)

            # 1. Collect all sender IDs and reader IDs
            sender_ids = {msg.sender_id for msg in messages}
            reader_ids = {
                receipt.user_id
                for msg in messages
                for receipt in msg.read_receipts
            }
            all_user_ids = list(sender_ids.union(reader_ids))

            # 2. Fetch all required user details in one go
            user_details_map = self._get_user_details_map(all_user_ids)

            # 3. Build the DTOs using the map
            message_dtos = []
            for msg in messages:
                sender_dto = user_details_map.get(msg.sender_id, UserDTO(id=msg.sender_id, name="Unknown User"))

                read_receipt_dtos = [
                    MessageReadReceiptDTO(
                        user=user_details_map.get(r.user_id, UserDTO(id=r.user_id, name="Unknown User")),
                        read_at=r.read_at
                    )
                    for r in msg.read_receipts
                ]

                message_dtos.append(MessageDTO(
                    id=msg.id, content=msg.content, sender=sender_dto,
                    created_at=msg.created_at, is_pinned=msg.is_pinned,
                    # attachments mapping would be here, it doesn't change
                    attachments=[],
                    read_receipts=read_receipt_dtos
                ))
            return message_dtos

    def send_message(self, sender_id: int, chat_id: int, content: str) -> Optional[MessageDTO]:
        """
        Validates and saves a new message, then returns its DTO.
        This is where the real-time broadcast would be triggered.
        """
        with self._session_provider.workspace() as session:
            # Authorization: Check if the user is actually a participant in the chat
            participant = self._chat_repo.get_participant_info(session, user_id=sender_id, chat_id=chat_id)
            if not participant:
                # Or raise a custom exception like NotAuthorizedError
                return None

            # Rule: In a channel, only admins can send messages
            if participant.chat.type == ChatType.CHANNEL and participant.role != ParticipantRole.ADMIN:
                return None

            new_message = self._chat_repo.create_message(session, chat_id, sender_id, content)

            # This is a critical step to ensure relationships are loaded before mapping
            session.flush()  # Flushes the above change to the DB transaction
            session.refresh(new_message)  # Refreshes the object with data from the DB

            # 1. Map the new message to a DTO
            message_dto = self._map_message_to_dto(new_message)

            if message_dto:
                self._client.send_message({
                    "type": "message",
                    "chat_id": chat_id,
                    "payload": message_dto.__dict__  # Convert DTO to dict for JSON
                })

            return message_dto

    def pin_message(self, user_id: int, message_id: int) -> bool:
        """Pins a message, but only if the user is an admin in that chat."""
        with self._session_provider.workspace() as session:
            message = session.get(MessageModel, message_id)
            if not message:
                return False

            # Authorization: Check if the user is an admin in this chat
            participant = self._chat_repo.get_participant_info(session, user_id=user_id, chat_id=message.chat_id)
            if not participant or participant.role != ParticipantRole.ADMIN:
                return False

            self._chat_repo.set_message_pin_status(session, message_id, is_pinned=True)
            # Here you would also trigger a real-time event to notify other clients of the pin
            return True

    def mark_message_as_read(self, user_id: int, message_id: int):
        """Marks a message as read for a user."""
        with self._session_provider.workspace() as session:
            self._chat_repo.mark_message_as_read(session, message_id, user_id)
            # Here you would trigger a real-time event to update the "seen by" list on other clients' screens
