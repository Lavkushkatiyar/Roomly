import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.enums import GuestLanguage


class RawInputCreate(BaseModel):
    room_id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    transcript: str = Field(min_length=1)
    guest_language: GuestLanguage


class RawInputResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    room_id: uuid.UUID
    conversation_id: uuid.UUID | None
    transcript: str
    guest_language: GuestLanguage
    created_at: datetime
