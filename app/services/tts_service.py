from app.providers.gnani.text_to_speech import GnaniTTS
from app.schemas.assistant import AssistantResponse
from app.schemas.providers.gnani import SpeechGenerationResult

TTS_VOICE_MAPPING = {
    "en-IN": "Shivani",
    "hi-IN": "Shivani",
    "hi-en": "Shivani",
    "ta-IN": "Shivani",
    "te-IN": "Shivani",
    "kn-IN": "Shivani",
    "ml-IN": "Shivani",
    "mr-IN": "Shivani",
    "bn-IN": "Shivani",
    "gu-IN": "Shivani",
    "pa-IN": "Shivani",
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
