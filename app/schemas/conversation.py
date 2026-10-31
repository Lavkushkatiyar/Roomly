from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

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
