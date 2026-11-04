import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.enums import GuestLanguage


class RawInput(Base):
    __tablename__ = "raw_inputs"

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
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("roomly_conversations.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    transcript: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    guest_language: Mapped[GuestLanguage] = mapped_column(
        Enum(GuestLanguage, name="guest_language"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
