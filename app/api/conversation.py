import uuid

import httpx
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.db.models.enums import MessageRole
from app.db.session import get_db
from app.providers.gnani.client import GnaniAPIError
from app.providers.gnani.dependencies import get_gnani_stt
from app.providers.gnani.stt import GnaniSTT
from app.providers.reasoning.llm_factory import get_reasoning_provider
from app.providers.reasoning.ollama import OllamaProvider
from app.schemas.conversation import ConversationCreate, ConversationResponse
from app.schemas.conversation_turn import ConversationTurnResponse
from app.services.conversation_services import ConversationServices
from app.services.voice_ingestion import VoiceIngestionServices

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


@router.post(
    "/",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    conversation_data: ConversationCreate,
    db: Session = Depends(get_db),
):
    try:
        conversation = ConversationServices.create_conversation(
            db=db,
            room_id=conversation_data.room_id,
            guest_language=conversation_data.guest_language,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return conversation


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
)
def get_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    conversation = ConversationServices.get_active_conversation(
        db=db,
        conversation_id=conversation_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active conversation not found",
        )

    return conversation


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
)
def get_all_conversations(
    db: Session = Depends(get_db),
):
    conversation = ConversationServices.get_all_conversations(db=db)

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active conversation not found",
        )

    return conversation


@router.post(
    "/{conversation_id}/end",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
)
def end_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    conversation = ConversationServices.end_conversation(
        db=db,
        conversation_id=conversation_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active conversation not found",
        )

    return conversation


@router.post(
    "/{conversation_id}/turns",
    response_model=ConversationTurnResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation_turn(
    conversation_id: uuid.UUID,
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    stt_provider: GnaniSTT = Depends(get_gnani_stt),
    reasoning_provider: OllamaProvider = Depends(get_reasoning_provider),
):
    conversation = ConversationServices.get_active_conversation(
        db=db,
        conversation_id=conversation_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active conversation not found.",
        )

    try:
        audio_data = await audio.read()

        ingestion_service = VoiceIngestionServices(
            stt_provider=stt_provider,
            reasoning_provider=reasoning_provider,
        )

        result = await ingestion_service.process_conversation_turn(
            db=db,
            audio=audio_data,
            filename=audio.filename or "recording.wav",
            room_id=conversation.room_id,
            guest_language=conversation.guest_language,
            conversation_id=conversation.id,
        )
        ConversationServices.save_message(
            db=db,
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=result.turn.assistant_response.text,
        )

        return result

    except httpx.HTTPStatusError as exc:
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
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Speech transcription service failed.",
        ) from exc

    finally:
        await audio.close()
