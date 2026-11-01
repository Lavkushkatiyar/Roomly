from typing import Protocol

from app.schemas.task_extraction import TaskExtractionResult


class ReasoningProvider(Protocol):
    async def extract_tasks(
        self,
        transcript: str,
    ) -> TaskExtractionResult: ...
