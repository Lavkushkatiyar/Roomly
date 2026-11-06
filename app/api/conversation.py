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

CONFIRMATION_RESPONSES = {
    GuestLanguage.ENGLISH: (
        "Your request is being sent to the hotel team. "
        "If you need anything else, please make a new request."
    ),
    GuestLanguage.Hindi: (
        "आपका अनुरोध होटल टीम को भेजा जा रहा है। "
        "अगर आपको किसी और चीज़ की ज़रूरत हो, तो कृपया नया अनुरोध करें।"
    ),
    GuestLanguage.HINGLISH: (
        "Aapka request hotel team ko bheja ja raha hai. "
        "Agar aapko kisi aur cheez ki zaroorat ho, toh kripya naya request karein."
    ),
    GuestLanguage.TAMIL: (
        "உங்கள் கோரிக்கை ஹோட்டல் குழுவிற்கு அனுப்பப்படுகிறது. "
        "வேறு ஏதாவது தேவைப்பட்டால், தயவுசெய்து புதிய கோரிக்கையைத் தொடங்குங்கள்."
    ),
    GuestLanguage.TELUGU: (
        "మీ అభ్యర్థన హోటల్ బృందానికి పంపబడుతోంది. మీకు వేరే ఏదైనా అవసరమైతే, దయచేసి కొత్త అభ్యర్థనను ప్రారంభించండి."
    ),
    GuestLanguage.KANNADA: (
        "ನಿಮ್ಮ ವಿನಂತಿಯನ್ನು ಹೋಟೆಲ್ ತಂಡಕ್ಕೆ ಕಳುಹಿಸಲಾಗುತ್ತಿದೆ. "
        "ಬೇರೆ ಏನಾದರೂ ಬೇಕಿದ್ದರೆ, ದಯವಿಟ್ಟು ಹೊಸ ವಿನಂತಿಯನ್ನು ಪ್ರಾರಂಭಿಸಿ."
    ),
    GuestLanguage.MALAYALAM: (
        "നിങ്ങളുടെ അഭ്യർത്ഥന ഹോട്ടൽ ടീമിന് അയയ്ക്കുകയാണ്. "
        "മറ്റെന്തെങ്കിലും ആവശ്യമുണ്ടെങ്കിൽ, ദയവായി പുതിയ അഭ്യർത്ഥന ആരംഭിക്കുക."
    ),
    GuestLanguage.MARATHI: (
        "आपली विनंती हॉटेल टीमकडे पाठवली जात आहे. आणखी काही हवे असल्यास, कृपया नवीन विनंती करा."
    ),
    GuestLanguage.BENGALI: (
        "আপনার অনুরোধটি হোটেল টিমের কাছে পাঠানো হচ্ছে। "
        "আর কিছু প্রয়োজন হলে, অনুগ্রহ করে নতুন অনুরোধ করুন।"
    ),
    GuestLanguage.GUJARATI: (
        "તમારી વિનંતી હોટેલ ટીમને મોકલવામાં આવી રહી છે. "
        "બીજું કંઈ જરૂરી હોય, તો કૃપા કરીને નવી વિનંતી કરો."
    ),
    GuestLanguage.PUNJABI: (
        "ਤੁਹਾਡੀ ਬੇਨਤੀ ਹੋਟਲ ਟੀਮ ਨੂੰ ਭੇਜੀ ਜਾ ਰਹੀ ਹੈ। ਹੋਰ ਕੁਝ ਚਾਹੀਦਾ ਹੋਵੇ, ਤਾਂ ਕਿਰਪਾ ਕਰਕੇ ਨਵੀਂ ਬੇਨਤੀ ਕਰੋ।"
    ),
}

CONVERSATION_CLOSING_RESPONSES = {
    GuestLanguage.ENGLISH: (
        "<excited> It was a pleasure assisting you. Have a wonderful day!"
    ),
    GuestLanguage.Hindi: "आपकी सहायता करके अच्छा लगा। आपका दिन शुभ हो!",
    GuestLanguage.HINGLISH: "आपकी मदद करके अच्छा लगा। आपका दिन शुभ हो!",
    GuestLanguage.TAMIL: "உங்களுக்கு உதவியதில் மகிழ்ச்சி. இனிய நாளாக அமையட்டும்!",
    GuestLanguage.TELUGU: "మీకు సహాయం చేయడం ఆనందంగా ఉంది. మీ రోజు శుభంగా ఉండాలి!",
    GuestLanguage.KANNADA: "ನಿಮಗೆ ಸಹಾಯ ಮಾಡಲು ಸಂತೋಷವಾಯಿತು. ನಿಮ್ಮ ದಿನ ಶುಭವಾಗಿರಲಿ!",
    GuestLanguage.MALAYALAM: "നിങ്ങളെ സഹായിച്ചതിൽ സന്തോഷം. നിങ്ങളുടെ ദിവസം ശുഭകരമാകട്ടെ!",
    GuestLanguage.MARATHI: "आपली मदत करताना आनंद झाला. आपला दिवस शुभ जावो!",
    GuestLanguage.BENGALI: "আপনাকে সাহায্য করতে পেরে ভালো লাগল। আপনার দিনটি শুভ হোক!",
    GuestLanguage.GUJARATI: "આપની મદદ કરીને આનંદ થયો. આપનો દિવસ શુભ રહે!",
    GuestLanguage.PUNJABI: "ਤੁਹਾਡੀ ਮਦਦ ਕਰਕੇ ਖੁਸ਼ੀ ਹੋਈ। ਤੁਹਾਡਾ ਦਿਨ ਚੰਗਾ ਲੰਘੇ!",
}

PENDING_CONFIRMATION_RESPONSES = {
    GuestLanguage.ENGLISH: (
        "I still have your request awaiting confirmation. Would you like me to send it?"
    ),
    GuestLanguage.Hindi: "आपका अनुरोध अभी पुष्टि के लिए बाकी है। क्या मैं इसे भेज दूँ?",
    GuestLanguage.HINGLISH: (
        "Aapka request abhi confirmation ke liye pending hai. Kya main ise bhej doon?"
    ),
    GuestLanguage.TAMIL: "உங்கள் கோரிக்கை இன்னும் உறுதிப்படுத்தப்படவில்லை. அதை அனுப்பவா?",
    GuestLanguage.TELUGU: "మీ అభ్యర్థన ఇంకా నిర్ధారణ కోసం వేచి ఉంది. దాన్ని పంపించనా?",
    GuestLanguage.KANNADA: "ನಿಮ್ಮ ವಿನಂತಿಗೆ ಇನ್ನೂ ದೃಢೀಕರಣ ಬೇಕಿದೆ. ಅದನ್ನು ಕಳುಹಿಸಬೇಕೇ?",
    GuestLanguage.MALAYALAM: "നിങ്ങളുടെ അഭ്യർത്ഥനയ്ക്ക് ഇനിയും സ്ഥിരീകരണം ആവശ്യമാണ്. അത് അയയ്ക്കട്ടേ?",
    GuestLanguage.MARATHI: "आपल्या विनंतीला अजून पुष्टी आवश्यक आहे. ती पाठवू का?",
    GuestLanguage.BENGALI: "আপনার অনুরোধটি এখনও নিশ্চিত করা হয়নি। এটি কি পাঠাব?",
    GuestLanguage.GUJARATI: "તમારી વિનંતીની હજી પુષ્ટિ બાકી છે. શું હું તેને મોકલું?",
    GuestLanguage.PUNJABI: "ਤੁਹਾਡੀ ਬੇਨਤੀ ਦੀ ਹਾਲੇ ਪੁਸ਼ਟੀ ਬਾਕੀ ਹੈ। ਕੀ ਮੈਂ ਇਸਨੂੰ ਭੇਜਾਂ?",
}

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
    if turn.intent == ConversationIntent.END_CONVERSATION and pending_tasks:
        turn = turn.model_copy(
            update={
                "intent": ConversationIntent.UNCLEAR,
                "tasks": [],
                "assistant_response": AssistantResponse(
                    text=PENDING_CONFIRMATION_RESPONSES[conversation.guest_language],
                    language=conversation.guest_language.value,
                ),
            }
        )
        result = result.model_copy(update={"turn": turn})

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
                        text=CONFIRMATION_RESPONSES[conversation.guest_language],
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
    elif conversation_ended:
        turn = turn.model_copy(
            update={
                "assistant_response": AssistantResponse(
                    text=CONVERSATION_CLOSING_RESPONSES[conversation.guest_language],
                    language=conversation.guest_language.value,
                )
            }
        )
        result = result.model_copy(update={"turn": turn})
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
