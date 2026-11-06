from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.assistant import AssistantResponse
from app.schemas.raw_input import RawInputResponse
from app.schemas.task_extraction import ProposedServiceRequest


class ConversationIntent(StrEnum):
    NEW_REQUEST = "NEW_REQUEST"
    CONFIRMATION = "CONFIRMATION"
    REJECTION = "REJECTION"
    MODIFICATION = "MODIFICATION"
    GENERAL_CONVERSATION = "GENERAL_CONVERSATION"
    UNCLEAR = "UNCLEAR"


class ConversationTurnResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: ConversationIntent
    tasks: list[ProposedServiceRequest] = Field(default_factory=list)
    assistant_response: AssistantResponse


class ConversationTurnAudio(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audio_base64: str
    content_type: str


class ConversationTurnProcessingResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_input: RawInputResponse
    turn: ConversationTurnResult


class ConversationTurnResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conversation_id: UUID
    conversation_ended: bool = False
    raw_input: RawInputResponse
    turn: ConversationTurnResult
    audio: ConversationTurnAudio
