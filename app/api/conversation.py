import base64
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

from app.db.models.conversation import Conversation
from app.db.models.enums import GuestLanguage
from app.db.session import get_db
from app.providers.gnani.client import GnaniAPIError
from app.providers.gnani.dependencies import get_gnani_stt, get_gnani_tts
from app.providers.gnani.stt import GnaniSTT
from app.providers.gnani.text_to_speech import GnaniTTS
from app.providers.reasoning.llm_factory import get_reasoning_provider
from app.providers.reasoning.ollama import OllamaProvider
from app.schemas.assistant import AssistantResponse
from app.schemas.conversation import ConversationCreate, ConversationResponse
from app.schemas.conversation_turn import (
    ConversationIntent,
    ConversationTurnAudio,
    ConversationTurnResponse,
)
from app.services.conversation_services import ConversationServices
from app.services.service_requests import ServiceRequestServices
from app.services.tts_service import TTSService
from app.services.voice_ingestion import VoiceIngestionServices

logger = logging.getLogger(__name__)

CONFIRMATION_RESPONSE = (
    "Your request is being sent to the hotel team. "
    "If you need anything else, please make a new request."
)

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


async def _process_audio_turn(
    *,
    conversation: Conversation,
    audio: UploadFile,
    db: Session,
    stt_provider: GnaniSTT,
    reasoning_provider: OllamaProvider,
    tts_provider: GnaniTTS,
) -> ConversationTurnResponse:
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
    except httpx.HTTPError as exc:
        logger.exception("Conversation speech or reasoning provider failed.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Conversation processing service failed.",
        ) from exc
    except GnaniAPIError as exc:
        logger.exception("Conversation speech provider failed.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Conversation processing service failed.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    finally:
        await audio.close()

    pending_raw_input_id, pending_tasks = ConversationServices.get_pending_proposal(
        db=db,
        conversation_id=conversation.id,
    )
    turn = result.turn
    conversation_ended = (
        turn.intent == ConversationIntent.END_CONVERSATION and not turn.tasks
    )
    confirmed_raw_input_id = None

    if turn.intent == ConversationIntent.CONFIRMATION:
        if pending_tasks:
            turn = turn.model_copy(update={"tasks": pending_tasks})
            turn = turn.model_copy(
                update={
                    "assistant_response": AssistantResponse(
                        text=CONFIRMATION_RESPONSE,
                        language=conversation.guest_language.value,
                    )
                }
            )
            result = result.model_copy(update={"turn": turn})
            confirmed_raw_input_id = pending_raw_input_id
            pending_tasks = []
            pending_raw_input_id = None
            conversation_ended = True
        else:
            turn = turn.model_copy(
                update={
                    "intent": ConversationIntent.UNCLEAR,
                    "tasks": [],
                }
            )
            result = result.model_copy(update={"turn": turn})
            pending_raw_input_id = None
    elif turn.intent == ConversationIntent.REJECTION:
        pending_tasks = []
        pending_raw_input_id = None
    elif turn.intent in (
        ConversationIntent.NEW_REQUEST,
        ConversationIntent.MODIFICATION,
    ):
        pending_tasks = turn.tasks
        pending_raw_input_id = result.raw_input.id if turn.tasks else None

    if conversation_ended:
        pending_tasks = []
        pending_raw_input_id = None

    try:
        speech = await TTSService(provider=tts_provider).generate_speech(
            assistant_response=turn.assistant_response,
        )
    except (GnaniAPIError, httpx.HTTPError, ValueError) as exc:
        logger.exception("Conversation response speech generation failed.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Speech generation service failed.",
        ) from exc

    if turn.intent == ConversationIntent.CONFIRMATION and turn.tasks:
        ServiceRequestServices.create_service_requests(
            db=db,
            raw_input_id=confirmed_raw_input_id or result.raw_input.id,
            requests=turn.tasks,
            commit=False,
        )

    ConversationServices.save_turn_message(
        db=db,
        conversation_id=conversation.id,
        content=turn.assistant_response.text,
        pending_tasks=pending_tasks,
        pending_raw_input_id=pending_raw_input_id,
    )

    if conversation_ended:
        ended_conversation = ConversationServices.end_conversation(
            db=db,
            conversation_id=conversation.id,
        )
        if ended_conversation is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conversation could not be ended.",
            )

    return ConversationTurnResponse(
        conversation_id=conversation.id,
        conversation_ended=conversation_ended,
        raw_input=result.raw_input,
        turn=turn,
        audio=ConversationTurnAudio(
            audio_base64=base64.b64encode(speech.audio_data).decode("ascii"),
            content_type=speech.content_type,
        ),
    )


@router.post(
    "/turns",
    response_model=ConversationTurnResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_or_continue_conversation_turn(
    audio: UploadFile = File(...),
    room_id: uuid.UUID = Form(...),
    guest_language: GuestLanguage = Form(...),
    conversation_id: uuid.UUID | None = Form(default=None),
    db: Session = Depends(get_db),
    stt_provider: GnaniSTT = Depends(get_gnani_stt),
    reasoning_provider: OllamaProvider = Depends(get_reasoning_provider),
    tts_provider: GnaniTTS = Depends(get_gnani_tts),
):
    if conversation_id is None:
        try:
            conversation = ConversationServices.create_conversation(
                db=db,
                room_id=room_id,
                guest_language=guest_language,
            )
        except ValueError as exc:
            await audio.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc
    else:
        conversation = ConversationServices.get_active_conversation(
            db=db,
            conversation_id=conversation_id,
        )
        if conversation is None:
            await audio.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active conversation not found.",
            )
        if (
            conversation.room_id != room_id
            or conversation.guest_language != guest_language
        ):
            await audio.close()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Room and language must match the active conversation.",
            )

    return await _process_audio_turn(
        conversation=conversation,
        audio=audio,
        db=db,
        stt_provider=stt_provider,
        reasoning_provider=reasoning_provider,
        tts_provider=tts_provider,
    )


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
    tts_provider: GnaniTTS = Depends(get_gnani_tts),
):
    conversation = ConversationServices.get_active_conversation(
        db=db,
        conversation_id=conversation_id,
    )

    if conversation is None:
        await audio.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active conversation not found.",
        )

    return await _process_audio_turn(
        conversation=conversation,
        audio=audio,
        db=db,
        stt_provider=stt_provider,
        reasoning_provider=reasoning_provider,
        tts_provider=tts_provider,
    )
