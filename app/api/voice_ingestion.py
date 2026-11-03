import logging
import uuid

import httpx
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
from app.providers.reasoning.llm_factory import get_reasoning_provider
from app.providers.reasoning.ollama import OllamaProvider
from app.schemas.voice_ingestion import VoiceIngestionResponse
from app.services.voice_ingestion import VoiceIngestionServices

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["Voice"])


@router.post(
    "/ingest",
    response_model=VoiceIngestionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_voice(
    audio: UploadFile = File(...),
    room_id: uuid.UUID = Form(...),
    guest_language: GuestLanguage = Form(...),
    db: Session = Depends(get_db),
    stt_provider: GnaniSTT = Depends(get_gnani_stt),
    ollama_provider: OllamaProvider = Depends(get_reasoning_provider),
):
    try:
        audio_data = await audio.read()

        ingestion_service = VoiceIngestionServices(
            stt_provider=stt_provider, reasoning_provider=ollama_provider
        )

        return await ingestion_service.ingest_and_extract(
            db=db,
            audio=audio_data,
            filename=audio.filename or "recording.wav",
            room_id=room_id,
            guest_language=guest_language,
        )

    except httpx.HTTPStatusError as exc:
        logger.error(
            "Gnani API rejected request: status=%s response=%s",
            exc.response.status_code,
            exc.response.text[:1000],
        )
        raise GnaniAPIError(
            "Gnani rejected the request.",
            status_code=exc.response.status_code,
        ) from exc

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
