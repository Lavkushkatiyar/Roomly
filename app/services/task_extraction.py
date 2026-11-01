import logging

from app.providers.reasoning.base import ReasoningProvider
from app.providers.reasoning.llm_factory import get_reasoning_provider
from app.schemas.task_extraction import TaskExtractionResult

logger = logging.getLogger(__name__)


class TaskExtractionServices:
    def __init__(
        self,
        reasoning_provider: ReasoningProvider | None = None,
    ) -> None:
        self.reasoning_provider = reasoning_provider or get_reasoning_provider()

    async def extract_tasks_from_text(
        self,
        transcript: str,
    ) -> TaskExtractionResult:
        normalized_transcript = transcript.strip()

        if not normalized_transcript:
            raise ValueError("Transcript cannot be empty.")

        logger.info("Starting task extraction from text.")

        result = await self.reasoning_provider.extract_tasks(
            transcript=normalized_transcript,
        )

        logger.info(
            "Task extraction completed. Proposed tasks=%d",
            len(result.tasks),
        )

        return result
