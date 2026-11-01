import logging

from app.core.config import settings
from app.db.models.enums import GuestLanguage
from app.providers.gnani.client import GnaniClient
from app.providers.gnani.stt import GnaniSTT
from app.providers.reasoning.ollama import OllamaProvider
from app.schemas.task_extraction import TaskExtractionResult

logger = logging.getLogger(__name__)


class TaskExtractionServices:
    def __init__(self) -> None:
        self.client = GnaniClient(
            settings.GNANI_API_KEY_ID,
            timeout=40.0,
        )
        self.stt_provider = GnaniSTT(client=self.client)
        self.reasoning_provider = OllamaProvider(
            model=settings.REASONING_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
        )

    async def extract_tasks_from_voice(
        self,
        audio: bytes,
        language: GuestLanguage = GuestLanguage.ENGLISH,
        filename: str = "guest-audio.wav",
    ) -> TaskExtractionResult:
        if not audio:
            raise ValueError("Audio input cannot be empty.")

        logger.info("Starting voice task extraction.")

        transcription = await self.stt_provider.transcribe(
            audio=audio,
            language=language,
            filename=filename,
        )

        transcript = transcription.text.strip()

        if not transcript:
            logger.warning("STT returned an empty transcript.")
            return TaskExtractionResult(tasks=[])

        logger.info(
            "STT completed. Provider=%s Model=%s",
            transcription.provider,
            transcription.model,
        )

        result = await self.reasoning_provider.extract_tasks(
            transcript=transcript,
        )

        logger.info(
            "Task extraction completed. Proposed tasks=%d",
            len(result.tasks),
        )

        return result
