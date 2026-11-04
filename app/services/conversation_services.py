import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.conversation import Conversation
from app.db.models.enums import ConversationStatus, GuestLanguage
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
