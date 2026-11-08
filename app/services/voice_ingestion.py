import logging
import time
import uuid

from sqlalchemy.orm import Session

from app.db.models.enums import GuestLanguage
from app.db.models.raw_input import RawInput
from app.providers.gnani.stt import GnaniSTT
from app.providers.reasoning.ollama import OllamaProvider
from app.schemas.conversation_turn import ConversationTurnProcessingResult
from app.schemas.raw_input import RawInputCreate, RawInputResponse
from app.schemas.voice_ingestion import VoiceIngestionResponse
from app.services.conversation_services import ConversationServices
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
        started_at = time.perf_counter()
        logger.info(
            "STT layer started | conversation_id=%s room_id=%s language=%s "
            "audio_bytes=%d",
            conversation_id,
            room_id,
            guest_language.value,
            len(audio),
        )
        transcription = await self.stt_provider.transcribe(
            audio=audio, language=guest_language.value, filename=filename
        )
        transcript = transcription.text.strip()
        logger.info(
            "STT layer passed | conversation_id=%s provider=%s provider_request_id=%s "
            "transcript_chars=%d duration_ms=%.0f",
            conversation_id,
            transcription.provider,
            transcription.request_id,
            len(transcript),
            (time.perf_counter() - started_at) * 1000,
        )

        if not transcript:
            logger.warning(
                "STT layer returned an empty transcript | conversation_id=%s",
                conversation_id,
            )
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
            "Guest message persisted | conversation_id=%s room_id=%s raw_input_id=%s",
            conversation_id,
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
        context = (
            ConversationServices.get_conversation_context(
                db=db,
                conversation_id=conversation_id,
            )
            if conversation_id is not None
            else None
        )

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
            context=context,
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

    async def process_conversation_turn(
        self,
        db: Session,
        audio: bytes,
        filename: str,
        room_id: uuid.UUID,
        guest_language: GuestLanguage,
        conversation_id: uuid.UUID,
    ) -> ConversationTurnProcessingResult:
        context = ConversationServices.get_conversation_context(
            db=db,
            conversation_id=conversation_id,
        )

        raw_input = await self.ingest_audio(
            db=db,
            audio=audio,
            filename=filename,
            room_id=room_id,
            guest_language=guest_language,
            conversation_id=conversation_id,
        )

        reasoning_started_at = time.perf_counter()
        logger.info(
            "Reasoning layer started | conversation_id=%s provider=%s "
            "language=%s context_messages=%d",
            conversation_id,
            type(self.reasoning_provider).__name__,
            guest_language.value,
            len(context),
        )
        turn = await self.reasoning_provider.process_turn(
            transcript=raw_input.transcript,
            language=raw_input.guest_language.value,
            context=context,
        )
        logger.info(
            "Reasoning layer passed | conversation_id=%s intent=%s "
            "proposed_tasks=%d duration_ms=%.0f",
            conversation_id,
            turn.intent.value,
            len(turn.tasks),
            (time.perf_counter() - reasoning_started_at) * 1000,
        )

        return ConversationTurnProcessingResult(
            raw_input=RawInputResponse.model_validate(raw_input),
            turn=turn,
        )
