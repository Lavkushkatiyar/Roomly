from fastapi import APIRouter, Depends

from app.providers.gnani.dependencies import get_gnani_tts
from app.providers.gnani.text_to_speech import GnaniTTS
from app.schemas.assistant import AssistantResponse
from app.services.tts_service import TTSService

router = APIRouter(prefix="/voice_generate", tags=["VOICE_GENERATION"])


@router.post("/")
async def convert_audio(
    response: AssistantResponse, tts_provider: GnaniTTS = Depends(get_gnani_tts)
):
    tts_service = TTSService(provider=tts_provider)
    speech_audio = await tts_service.generate_speech(assistant_response=response)
    return speech_audio
