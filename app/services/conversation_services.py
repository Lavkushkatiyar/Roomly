import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.conversation import Conversation
from app.db.models.conversation_message import ConversationMessage
from app.db.models.enums import ConversationStatus, GuestLanguage, MessageRole
from app.db.models.hotel_room import HotelRoom
from app.db.models.raw_input import RawInput


class ConversationServices:
    @staticmethod
    def create_conversation(
        db: Session,
        room_id: uuid.UUID,
        guest_language: GuestLanguage,
    ) -> Conversation:
        room = db.get(HotelRoom, room_id)

        if room is None or not room.is_active:
            raise ValueError("Invalid or inactive hotel room")

        conversation = Conversation(
            room_id=room_id,
            guest_language=guest_language,
            status=ConversationStatus.ACTIVE,
        )

        try:
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        except SQLAlchemyError:
            db.rollback()
            raise

        return conversation

    @staticmethod
    def get_active_conversation(
        db: Session,
        conversation_id: uuid.UUID,
    ) -> Conversation | None:
        statement = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.status == ConversationStatus.ACTIVE,
        )

        return db.scalar(statement)

    @staticmethod
    def get_all_conversations(
        db: Session,
    ):
        statement = select(Conversation)
        return list(db.scalars(statement).all())

    @staticmethod
    def save_message(
        db: Session,
        conversation_id: uuid.UUID,
        role: MessageRole,
        content: str,
    ) -> ConversationMessage:
        conversation = ConversationServices.get_active_conversation(
            db,
            conversation_id,
        )

        if conversation is None:
            raise ValueError("Conversation does not exist or has ended")

        message = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content.strip(),
        )

        try:
            db.add(message)
            db.commit()
            db.refresh(message)
        except SQLAlchemyError:
            db.rollback()
            raise

        return message

    @staticmethod
    def _validate_conversation(
        db: Session,
        conversation_id: uuid.UUID,
    ) -> None:
        conversation = ConversationServices.get_active_conversation(
            db=db,
            conversation_id=conversation_id,
        )

        if conversation is None:
            raise ValueError("Active conversation not found.")

    @staticmethod
    def _get_guest_messages(
        db: Session,
        conversation_id: uuid.UUID,
    ) -> list[dict]:
        guest_messages = db.execute(
            select(RawInput.transcript, RawInput.created_at).where(
                RawInput.conversation_id == conversation_id
            )
        ).all()

        return [
            {
                "role": MessageRole.GUEST.value,
                "content": content,
                "created_at": created_at,
            }
            for content, created_at in guest_messages
        ]

    @staticmethod
    def _get_assistant_messages(
        db: Session,
        conversation_id: uuid.UUID,
    ) -> list[dict]:
        assistant_messages = db.execute(
            select(ConversationMessage.content, ConversationMessage.created_at).where(
                ConversationMessage.conversation_id == conversation_id,
                ConversationMessage.role == MessageRole.ASSISTANT,
            )
        ).all()

        return [
            {
                "role": MessageRole.ASSISTANT.value,
                "content": content,
                "created_at": created_at,
            }
            for content, created_at in assistant_messages
        ]

    @staticmethod
    def get_conversation_context(
        db: Session,
        conversation_id: uuid.UUID,
        limit: int = 10,
    ) -> list[dict[str, str]]:
        ConversationServices._validate_conversation(
            db=db,
            conversation_id=conversation_id,
        )

        guest_messages = ConversationServices._get_guest_messages(
            db=db,
            conversation_id=conversation_id,
        )

        assistant_messages = ConversationServices._get_assistant_messages(
            db=db,
            conversation_id=conversation_id,
        )

        messages = guest_messages + assistant_messages
        messages.sort(key=lambda message: message["created_at"])

        return [
            {"role": message["role"], "content": message["content"]}
            for message in messages[-limit:]
        ]

    @staticmethod
    def end_conversation(
        db: Session,
        conversation_id: uuid.UUID,
    ) -> Conversation | None:
        conversation = ConversationServices.get_active_conversation(
            db,
            conversation_id,
        )

        if conversation is None:
            return None

        conversation.status = ConversationStatus.ENDED
        conversation.ended_at = datetime.now(UTC)

        try:
            db.commit()
            db.refresh(conversation)
        except SQLAlchemyError:
            db.rollback()
            raise

        return conversation
