import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.conversation import Conversation
from app.db.models.conversation_message import ConversationMessage
from app.db.models.enums import ConversationStatus, GuestLanguage, MessageRole
from app.db.models.hotel_room import HotelRoom


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
    def get_conversation_context(
        db: Session,
        conversation_id: uuid.UUID,
        limit: int = 10,
    ) -> list[ConversationMessage]:
        statement = (
            select(ConversationMessage)
            .join(
                Conversation,
                Conversation.id == ConversationMessage.conversation_id,
            )
            .where(
                Conversation.id == conversation_id,
                Conversation.status == ConversationStatus.ACTIVE,
            )
            .order_by(ConversationMessage.created_at.desc())
            .limit(limit)
        )

        messages = list(db.scalars(statement).all())

        return list(reversed(messages))
