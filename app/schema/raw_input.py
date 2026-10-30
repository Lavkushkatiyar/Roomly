import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.enums import GuestLanguage


class RawInputCreate(BaseModel):
    room_id: uuid.UUID
    transcript: str = Field(min_length=1)
    guest_language: GuestLanguage


class RawInputResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    room_id: uuid.UUID
    transcript: str
    guest_language: GuestLanguage
    created_at: datetime
