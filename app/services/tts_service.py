from app.providers.gnani.text_to_speech import GnaniTTS
from app.schemas.assistant import AssistantResponse
from app.schemas.providers.gnani import SpeechGenerationResult


class TTSService:
    def __init__(self, provider: GnaniTTS) -> None:
        self.provider = provider

    async def generate_speech(
        self,
        assistant_response: AssistantResponse,
    ) -> SpeechGenerationResult:
        voice = "Avinash"
        language_code = assistant_response.language

        return await self.provider.generate_voice(
            text=assistant_response.text,
            language_code=language_code,
            voice=voice,
        )
