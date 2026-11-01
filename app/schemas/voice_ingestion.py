from pydantic import BaseModel

from app.schemas.raw_input import RawInputResponse
from app.schemas.task_extraction import TaskExtractionResult


class VoiceIngestionResponse(BaseModel):
    raw_input: RawInputResponse
    extraction: TaskExtractionResult
