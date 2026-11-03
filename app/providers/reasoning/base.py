from typing import Protocol

from app.schemas.assistant import AssistantResponse
from app.schemas.task_extraction import TaskExtractionResult


class ReasoningProvider(Protocol):
    async def extract_tasks(
        self,
        transcript: str,
    ) -> TaskExtractionResult: ...

    async def generate_response(
        self,
        extraction: TaskExtractionResult,
        language: str,
    ) -> AssistantResponse: ...
