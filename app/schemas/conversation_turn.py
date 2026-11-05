from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.assistant import AssistantResponse
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
