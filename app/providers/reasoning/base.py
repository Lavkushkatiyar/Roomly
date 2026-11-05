from typing import Protocol

from app.schemas.assistant import AssistantResponse
from app.schemas.conversation_turn import ConversationTurnResult
from app.schemas.task_extraction import TaskExtractionResult


class ReasoningProvider(Protocol):
    async def process_turn(
        self,
        transcript: str,
        language: str,
        context: list[dict[str, str]] | None = None,
    ) -> ConversationTurnResult: ...

    async def extract_tasks(
        self,
        transcript: str,
        context: list[dict[str, str]] | None = None,
    ) -> TaskExtractionResult: ...

    async def generate_response(
        self,
        extraction: TaskExtractionResult,
        language: str,
    ) -> AssistantResponse: ...
