import base64
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db.models.conversation import Conversation
from app.db.models.enums import (
    ConversationStatus,
    GuestLanguage,
    RequestCategory,
    RequestPriority,
)
from app.schemas.assistant import AssistantResponse
from app.schemas.conversation_turn import (
    ConversationIntent,
    ConversationTurnProcessingResult,
    ConversationTurnResult,
)
from app.schemas.raw_input import RawInputResponse
from app.schemas.task_extraction import ProposedServiceRequest
from app.services.conversation_services import ConversationServices
from app.services.voice_ingestion import VoiceIngestionServices


@pytest.mark.asyncio
async def test_conversation_turn_processes_and_persists_confirmation():
    conversation_id = uuid.uuid4()
    room_id = uuid.uuid4()
    raw_input_id = uuid.uuid4()
    request_raw_input_id = uuid.uuid4()
    task = ProposedServiceRequest(
        category=RequestCategory.HOUSEKEEPING,
        staff_summary="Deliver two towels",
        priority=RequestPriority.MEDIUM,
    )
    raw_input = RawInputResponse(
        id=raw_input_id,
        room_id=room_id,
        conversation_id=conversation_id,
        transcript="Yes, please",
        guest_language=GuestLanguage.ENGLISH,
        created_at=datetime.now(UTC),
    )
    turn = ConversationTurnResult(
        intent=ConversationIntent.CONFIRMATION,
        tasks=[],
        assistant_response=AssistantResponse(
            text="Thank you. I will send that request.",
            language=GuestLanguage.ENGLISH.value,
        ),
    )
    processing_result = ConversationTurnProcessingResult(
        raw_input=raw_input,
        turn=turn,
    )
    conversation = Conversation(
        id=conversation_id,
        room_id=room_id,
        guest_language=GuestLanguage.ENGLISH,
        status=ConversationStatus.ACTIVE,
    )
    audio = MagicMock()
    audio.filename = "recording.wav"
    audio.read = AsyncMock(return_value=b"recording")
    audio.close = AsyncMock()
    ingestion_service = MagicMock()
    ingestion_service.process_conversation_turn = AsyncMock(
        return_value=processing_result,
    )
    tts_service = MagicMock()
    tts_service.generate_speech = AsyncMock(
        return_value=SimpleNamespace(
            audio_data=b"wav audio",
            content_type="audio/wav",
        ),
    )
    db = MagicMock()

    with (
        patch(
            "app.api.conversation.VoiceIngestionServices",
            return_value=ingestion_service,
        ),
        patch(
            "app.api.conversation.ConversationServices.get_pending_proposal",
            return_value=(request_raw_input_id, [task]),
        ),
        patch(
            "app.api.conversation.TTSService",
            return_value=tts_service,
        ),
        patch(
            "app.api.conversation.ServiceRequestServices.create_service_requests",
        ) as create_requests,
        patch(
            "app.api.conversation.ConversationServices.save_turn_message",
        ) as save_turn_message,
    ):
        from app.api.conversation import _process_audio_turn

        result = await _process_audio_turn(
            conversation=conversation,
            audio=audio,
            db=db,
            stt_provider=MagicMock(),
            reasoning_provider=MagicMock(),
            tts_provider=MagicMock(),
        )

    ingestion_service.process_conversation_turn.assert_awaited_once()
    create_requests.assert_called_once_with(
        db=db,
        raw_input_id=request_raw_input_id,
        requests=[task],
        commit=False,
    )
    save_turn_message.assert_called_once_with(
        db=db,
        conversation_id=conversation_id,
        content=turn.assistant_response.text,
        pending_tasks=[],
        pending_raw_input_id=None,
    )
    tts_service.generate_speech.assert_awaited_once_with(
        assistant_response=turn.assistant_response,
    )
    assert result.conversation_id == conversation_id
    assert result.turn.tasks == [task]
    assert base64.b64decode(result.audio.audio_base64) == b"wav audio"
    assert result.audio.content_type == "audio/wav"
    audio.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_conversation_turn_makes_one_reasoning_call():
    conversation_id = uuid.uuid4()
    raw_input = SimpleNamespace(
        id=uuid.uuid4(),
        room_id=uuid.uuid4(),
        conversation_id=conversation_id,
        transcript="Please bring towels",
        guest_language=GuestLanguage.ENGLISH,
        created_at=datetime.now(UTC),
    )
    turn = ConversationTurnResult(
        intent=ConversationIntent.NEW_REQUEST,
        tasks=[],
        assistant_response=AssistantResponse(
            text="How many towels would you like?",
            language=GuestLanguage.ENGLISH.value,
        ),
    )
    reasoning_provider = MagicMock()
    reasoning_provider.process_turn = AsyncMock(return_value=turn)
    service = VoiceIngestionServices(
        stt_provider=MagicMock(),
        reasoning_provider=reasoning_provider,
    )
    service.ingest_audio = AsyncMock(return_value=raw_input)

    with patch.object(
        ConversationServices,
        "get_conversation_context",
        return_value=[],
    ):
        result = await service.process_conversation_turn(
            db=MagicMock(),
            audio=b"recording",
            filename="recording.wav",
            room_id=uuid.uuid4(),
            guest_language=GuestLanguage.ENGLISH,
            conversation_id=conversation_id,
        )

    reasoning_provider.process_turn.assert_awaited_once_with(
        transcript=raw_input.transcript,
        language=GuestLanguage.ENGLISH.value,
        context=[],
    )
    assert result.turn is turn


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("intent", "transcript", "conversation_ended"),
    [
        (
            ConversationIntent.END_CONVERSATION,
            "धन्यवाद, अब कोई अनुरोध नहीं है",
            True,
        ),
        (
            ConversationIntent.GENERAL_CONVERSATION,
            "Hello, how are you?",
            False,
        ),
    ],
)
async def test_conversation_end_intent_controls_closing(
    intent,
    transcript,
    conversation_ended,
):
    conversation_id = uuid.uuid4()
    room_id = uuid.uuid4()
    raw_input = RawInputResponse(
        id=uuid.uuid4(),
        room_id=room_id,
        conversation_id=conversation_id,
        transcript=transcript,
        guest_language=GuestLanguage.ENGLISH,
        created_at=datetime.now(UTC),
    )
    turn = ConversationTurnResult(
        intent=intent,
        tasks=[],
        assistant_response=AssistantResponse(
            text="You're welcome. Goodbye!",
            language=GuestLanguage.ENGLISH.value,
        ),
    )
    processing_result = ConversationTurnProcessingResult(
        raw_input=raw_input,
        turn=turn,
    )
    conversation = Conversation(
        id=conversation_id,
        room_id=room_id,
        guest_language=GuestLanguage.ENGLISH,
        status=ConversationStatus.ACTIVE,
    )
    audio = MagicMock()
    audio.filename = "recording.wav"
    audio.read = AsyncMock(return_value=b"recording")
    audio.close = AsyncMock()
    ingestion_service = MagicMock()
    ingestion_service.process_conversation_turn = AsyncMock(
        return_value=processing_result,
    )
    tts_service = MagicMock()
    tts_service.generate_speech = AsyncMock(
        return_value=SimpleNamespace(
            audio_data=b"wav audio",
            content_type="audio/wav",
        ),
    )
    db = MagicMock()

    with (
        patch(
            "app.api.conversation.VoiceIngestionServices",
            return_value=ingestion_service,
        ),
        patch(
            "app.api.conversation.ConversationServices.get_pending_proposal",
            return_value=(None, []),
        ),
        patch(
            "app.api.conversation.ConversationServices.save_turn_message",
        ) as save_turn_message,
        patch(
            "app.api.conversation.ConversationServices.end_conversation",
            return_value=conversation,
        ) as end_conversation,
        patch(
            "app.api.conversation.TTSService",
            return_value=tts_service,
        ),
    ):
        from app.api.conversation import _process_audio_turn

        result = await _process_audio_turn(
            conversation=conversation,
            audio=audio,
            db=db,
            stt_provider=MagicMock(),
            reasoning_provider=MagicMock(),
            tts_provider=MagicMock(),
        )

    if conversation_ended:
        end_conversation.assert_called_once_with(
            db=db,
            conversation_id=conversation_id,
        )
    else:
        end_conversation.assert_not_called()
    save_turn_message.assert_called_once_with(
        db=db,
        conversation_id=conversation_id,
        content=turn.assistant_response.text,
        pending_tasks=[],
        pending_raw_input_id=None,
    )
    assert result.conversation_ended is conversation_ended
