from app.providers.gnani.text_to_speech import GnaniTTS
from app.schemas.assistant import AssistantResponse
from app.schemas.providers.gnani import SpeechGenerationResult

TTS_VOICE_MAPPING = {
    "en-IN": "Kaveri",
    "hi-IN": "Nalini",
    "hi-en": "Poorvi",
    "ta-IN": "Asmita",
    "te-IN": "Suhana",
    "kn-IN": "Saanvi",
    "ml-IN": "Reshma",
    "mr-IN": "Zahira",
    "bn-IN": "Kirra",
    "gu-IN": "Falak",
    "pa-IN": "Mehuli",
}


class TTSService:
    def __init__(self, provider: GnaniTTS) -> None:
        self.provider = provider

    async def generate_speech(
        self,
        assistant_response: AssistantResponse,
    ) -> SpeechGenerationResult:
        language_code = assistant_response.language
        voice = TTS_VOICE_MAPPING.get(language_code, "Avinash")

        return await self.provider.generate_voice(
            text=assistant_response.text,
            language_code=language_code,
            voice=voice,
        )
