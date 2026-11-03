from pydantic import BaseModel

from app.schemas.assistant import AssistantResponse
from app.schemas.raw_input import RawInputResponse
from app.schemas.task_extraction import TaskExtractionResult


class VoiceIngestionResponse(BaseModel):
    raw_input: RawInputResponse
    extraction: TaskExtractionResult
    assistant_response: AssistantResponse
