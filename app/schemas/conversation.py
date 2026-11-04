from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.enums import ConversationStatus, GuestLanguage
from app.schemas.enums import ResponseType


class AudioOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    url: str | None = None
    content_type: str | None = None
    provider: str | None = None
    model: str | None = None


class AssistantResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    response_id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    text: str
    language: str
    response_type: ResponseType
    audio: AudioOutput | None = None


class ConversationCreate:
    model_config = ConfigDict(extra="ignore")

    room_id: UUID
    guest_language: GuestLanguage


class ConversationResponse:
    model_config = ConfigDict(extra="ignore")

    id: UUID
    room_id: UUID
    guest_language: GuestLanguage
    status: ConversationStatus
    started_at: datetime
    ended_at: datetime | None
