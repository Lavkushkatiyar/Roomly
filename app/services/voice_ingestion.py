import logging
import uuid

from sqlalchemy.orm import Session

from app.db.models.enums import GuestLanguage
from app.db.models.raw_input import RawInput
from app.providers.gnani.stt import GnaniSTT
from app.providers.reasoning.ollama import OllamaProvider
from app.schemas.raw_input import RawInputCreate, RawInputResponse
from app.schemas.voice_ingestion import VoiceIngestionResponse
from app.services.raw_input_services import RawInputServices
from app.services.task_extraction import TaskExtractionServices

logger = logging.getLogger(__name__)


class VoiceIngestionServices:
    def __init__(
        self,
        stt_provider: GnaniSTT,
        reasoning_provider: OllamaProvider,
        task_extraction_service: TaskExtractionServices | None = None,
    ) -> None:
        self.stt_provider = stt_provider
        self.reasoning_provider = reasoning_provider
        self.task_extraction_service = (
            task_extraction_service or TaskExtractionServices()
        )

    async def ingest_audio(
        self,
        db: Session,
        audio: bytes,
        filename: str,
        room_id: uuid.UUID,
        guest_language: GuestLanguage,
        conversation_id: uuid.UUID | None = None,
    ) -> RawInput:
        transcription = await self.stt_provider.transcribe(
            audio=audio, language=guest_language.value, filename=filename
        )
        transcript = transcription.text.strip()

        if not transcript:
            raise ValueError("Transcription can not be empty")

        raw_input_data = RawInputCreate(
            room_id=room_id,
            conversation_id=conversation_id,
            transcript=transcript,
            guest_language=guest_language,
        )

        raw_input = RawInputServices.create_raw_input(
            db=db,
            raw_input_data=raw_input_data,
        )

        logger.info(
            "Voice ingestion completed for room_id=%s, raw_input_id=%s",
            room_id,
            raw_input.id,
        )

        return raw_input

    async def ingest_and_extract(
        self,
        db: Session,
        audio: bytes,
        filename: str,
        room_id: uuid.UUID,
        guest_language: GuestLanguage,
        conversation_id: uuid.UUID | None = None,
    ) -> VoiceIngestionResponse:
        raw_input = await self.ingest_audio(
            db=db,
            audio=audio,
            filename=filename,
            room_id=room_id,
            guest_language=guest_language,
            conversation_id=conversation_id,
        )
        extraction = await self.task_extraction_service.extract_tasks_from_text(
            transcript=raw_input.transcript,
        )
        assistant_response = await self.reasoning_provider.generate_response(
            extraction=extraction,
            language=raw_input.guest_language.value,
        )

        return VoiceIngestionResponse(
            raw_input=RawInputResponse.model_validate(raw_input),
            extraction=extraction,
            assistant_response=assistant_response,
        )
