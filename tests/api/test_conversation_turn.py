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
@pytest.mark.parametrize(
    ("guest_language", "confirmation_response"),
    [
        (
            GuestLanguage.ENGLISH,
            "Your request is being sent to the hotel team. "
            "If you need anything else, please make a new request.",
        ),
        (
            GuestLanguage.Hindi,
            "आपका अनुरोध होटल टीम को भेजा जा रहा है। "
            "अगर आपको किसी और चीज़ की ज़रूरत हो, तो कृपया नया अनुरोध करें।",
        ),
        (
            GuestLanguage.HINGLISH,
            "Aapka request hotel team ko bheja ja raha hai. "
            "Agar aapko kisi aur cheez ki zaroorat ho, toh kripya naya request karein.",
        ),
        (
            GuestLanguage.TAMIL,
            "உங்கள் கோரிக்கை ஹோட்டல் குழுவிற்கு அனுப்பப்படுகிறது. "
            "வேறு ஏதாவது தேவைப்பட்டால், தயவுசெய்து புதிய கோரிக்கையைத் தொடங்குங்கள்.",
        ),
        (
            GuestLanguage.TELUGU,
            "మీ అభ్యర్థన హోటల్ బృందానికి పంపబడుతోంది. "
            "మీకు వేరే ఏదైనా అవసరమైతే, దయచేసి కొత్త అభ్యర్థనను ప్రారంభించండి.",
        ),
        (
            GuestLanguage.KANNADA,
            "ನಿಮ್ಮ ವಿನಂತಿಯನ್ನು ಹೋಟೆಲ್ ತಂಡಕ್ಕೆ ಕಳುಹಿಸಲಾಗುತ್ತಿದೆ. "
            "ಬೇರೆ ಏನಾದರೂ ಬೇಕಿದ್ದರೆ, ದಯವಿಟ್ಟು ಹೊಸ ವಿನಂತಿಯನ್ನು ಪ್ರಾರಂಭಿಸಿ.",
        ),
        (
            GuestLanguage.MALAYALAM,
            "നിങ്ങളുടെ അഭ്യർത്ഥന ഹോട്ടൽ ടീമിന് അയയ്ക്കുകയാണ്. "
            "മറ്റെന്തെങ്കിലും ആവശ്യമുണ്ടെങ്കിൽ, ദയവായി പുതിയ അഭ്യർത്ഥന ആരംഭിക്കുക.",
        ),
        (
            GuestLanguage.MARATHI,
            "आपली विनंती हॉटेल टीमकडे पाठवली जात आहे. "
            "आणखी काही हवे असल्यास, कृपया नवीन विनंती करा.",
        ),
        (
            GuestLanguage.BENGALI,
            "আপনার অনুরোধটি হোটেল টিমের কাছে পাঠানো হচ্ছে। "
            "আর কিছু প্রয়োজন হলে, অনুগ্রহ করে নতুন অনুরোধ করুন।",
        ),
        (
            GuestLanguage.GUJARATI,
            "તમારી વિનંતી હોટેલ ટીમને મોકલવામાં આવી રહી છે. "
            "બીજું કંઈ જરૂરી હોય, તો કૃપા કરીને નવી વિનંતી કરો.",
        ),
        (
            GuestLanguage.PUNJABI,
            "ਤੁਹਾਡੀ ਬੇਨਤੀ ਹੋਟਲ ਟੀਮ ਨੂੰ ਭੇਜੀ ਜਾ ਰਹੀ ਹੈ। "
            "ਹੋਰ ਕੁਝ ਚਾਹੀਦਾ ਹੋਵੇ, ਤਾਂ ਕਿਰਪਾ ਕਰਕੇ ਨਵੀਂ ਬੇਨਤੀ ਕਰੋ।",
        ),
    ],
)
async def test_conversation_turn_processes_and_persists_confirmation(
    guest_language,
    confirmation_response,
):
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
        guest_language=guest_language,
        created_at=datetime.now(UTC),
    )
    turn = ConversationTurnResult(
        intent=ConversationIntent.CONFIRMATION,
        tasks=[],
        assistant_response=AssistantResponse(
            text="Thank you. I will send that request.",
            language=guest_language.value,
        ),
    )
    processing_result = ConversationTurnProcessingResult(
        raw_input=raw_input,
        turn=turn,
    )
    conversation = Conversation(
        id=conversation_id,
        room_id=room_id,
        guest_language=guest_language,
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
        patch(
            "app.api.conversation.ConversationServices.end_conversation",
            return_value=conversation,
        ) as end_conversation,
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
        content=confirmation_response,
        pending_tasks=[],
        pending_raw_input_id=None,
    )
    tts_service.generate_speech.assert_awaited_once_with(
        assistant_response=AssistantResponse(
            text=confirmation_response,
            language=guest_language.value,
        ),
    )
    end_conversation.assert_called_once_with(
        db=db,
        conversation_id=conversation_id,
    )
    assert result.conversation_id == conversation_id
    assert result.conversation_ended
    assert result.turn.tasks == [task]
    assert result.turn.assistant_response.text == confirmation_response
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
    (
        "intent",
        "transcript",
        "guest_language",
        "has_pending_proposal",
        "expected_intent",
        "conversation_ended",
        "response_text",
    ),
    [
        (
            ConversationIntent.END_CONVERSATION,
            "धन्यवाद, अब कोई अनुरोध नहीं है",
            GuestLanguage.ENGLISH,
            False,
            ConversationIntent.END_CONVERSATION,
            True,
            "<excited> It was a pleasure assisting you. Have a wonderful day!",
        ),
        (
            ConversationIntent.END_CONVERSATION,
            "धन्यवाद, अब कोई अनुरोध नहीं है",
            GuestLanguage.Hindi,
            False,
            ConversationIntent.END_CONVERSATION,
            True,
            "आपकी सहायता करके अच्छा लगा। आपका दिन शुभ हो!",
        ),
        (
            ConversationIntent.END_CONVERSATION,
            "Yes, thank you, goodbye",
            GuestLanguage.ENGLISH,
            True,
            ConversationIntent.UNCLEAR,
            False,
            (
                "I still have your request awaiting confirmation. "
                "Would you like me to send it?"
            ),
        ),
        (
            ConversationIntent.GENERAL_CONVERSATION,
            "Hello, how are you?",
            GuestLanguage.ENGLISH,
            False,
            ConversationIntent.GENERAL_CONVERSATION,
            False,
            "You're welcome. Goodbye!",
        ),
        (
            ConversationIntent.CONFIRMATION,
            "Yes",
            GuestLanguage.ENGLISH,
            False,
            ConversationIntent.UNCLEAR,
            False,
            "You're welcome. Goodbye!",
        ),
    ],
)
async def test_conversation_end_intent_controls_closing(
    intent,
    transcript,
    guest_language,
    has_pending_proposal,
    expected_intent,
    conversation_ended,
    response_text,
):
    conversation_id = uuid.uuid4()
    room_id = uuid.uuid4()
    raw_input = RawInputResponse(
        id=uuid.uuid4(),
        room_id=room_id,
        conversation_id=conversation_id,
        transcript=transcript,
        guest_language=guest_language,
        created_at=datetime.now(UTC),
    )
    pending_raw_input_id = uuid.uuid4()
    pending_task = ProposedServiceRequest(
        category=RequestCategory.HOUSEKEEPING,
        staff_summary="Deliver two towels",
        priority=RequestPriority.MEDIUM,
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
        guest_language=guest_language,
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
            return_value=(
                (pending_raw_input_id, [pending_task])
                if has_pending_proposal
                else (None, [])
            ),
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
        patch(
            "app.api.conversation.ServiceRequestServices.create_service_requests",
        ) as create_requests,
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
        content=response_text,
        pending_tasks=[pending_task] if has_pending_proposal else [],
        pending_raw_input_id=pending_raw_input_id if has_pending_proposal else None,
    )
    assert result.conversation_ended is conversation_ended
    assert result.turn.intent == expected_intent
    if expected_intent == ConversationIntent.END_CONVERSATION:
        assert result.turn.assistant_response == AssistantResponse(
            text=response_text,
            language=guest_language.value,
        )
    if has_pending_proposal:
        create_requests.assert_not_called()
        assert result.turn.assistant_response == AssistantResponse(
            text=response_text,
            language=guest_language.value,
        )
