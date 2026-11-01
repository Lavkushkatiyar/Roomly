import logging
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.db.models.enums import GuestLanguage
from app.db.session import get_db
from app.providers.gnani.client import GnaniAPIError
from app.providers.gnani.dependencies import get_gnani_stt
from app.providers.gnani.stt import GnaniSTT
from app.schemas.raw_input import RawInputResponse
from app.services.voice_ingestion import VoiceIngestionServices

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["Voice"])


@router.post(
    "/ingest",
    response_model=RawInputResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_voice(
    audio: UploadFile = File(...),
    room_id: uuid.UUID = Form(...),
    guest_language: GuestLanguage = Form(...),
    db: Session = Depends(get_db),
    stt_provider: GnaniSTT = Depends(get_gnani_stt),
):
    try:
        audio_data = await audio.read()

        ingestion_service = VoiceIngestionServices(
            stt_provider=stt_provider,
        )

        return await ingestion_service.ingest_audio(
            db=db,
            audio=audio_data,
            filename=audio.filename or "recording.wav",
            room_id=room_id,
            guest_language=guest_language,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except GnaniAPIError as exc:
        logger.exception("Voice transcription failed.")

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Speech transcription service failed.",
        ) from exc

    finally:
        await audio.close()
