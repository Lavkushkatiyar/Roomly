import logging
import uuid

from sqlalchemy.orm import Session

from app.db.models.enums import GuestLanguage
from app.db.models.raw_input import RawInput
from app.providers.gnani.stt import GnaniSTT
from app.schemas.raw_input import RawInputCreate
from app.services.raw_input_services import RawInputServices

logger = logging.getLogger(__name__)


class VoiceIngestionServices:
    def __init__(self, stt_provider: GnaniSTT) -> None:
        self.stt_provider = stt_provider

    async def ingest_audio(
        self,
        db: Session,
        audio: bytes,
        filename: str,
        room_id: uuid.UUID,
        guest_language: GuestLanguage,
    ) -> RawInput:
        transcription = await self.stt_provider.transcribe(
            audio=audio, language=guest_language.value, filename=filename
        )

        transcript = transcription.text.strip()
        if not transcription:
            raise ValueError("Transcription can not be empty")

        raw_input_data = RawInputCreate(
            room_id=room_id, transcript=transcript, guest_language=guest_language
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
