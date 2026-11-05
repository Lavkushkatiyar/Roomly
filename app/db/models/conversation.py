import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.enums import ConversationStatus, GuestLanguage


class Conversation(Base):
    __tablename__ = "roomly_conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    room_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("hotel_rooms.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    guest_language: Mapped[GuestLanguage] = mapped_column(
        Enum(
            GuestLanguage,
            name="roomly_guest_language",
            create_type=False,
        ),
        nullable=False,
    )

    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus, name="roomly_conversation_status"),
        default=ConversationStatus.ACTIVE,
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
