from app.core.config import settings
from app.db.models.enums import GuestLanguage
from app.providers.gnani.client import GnaniClient
from app.providers.gnani.stt import GnaniSTT
from app.providers.reasoning.ollama import OllamaProvider


class TaskExtractionServices:
    def __init__(self) -> None:
        self.provider = OllamaProvider()
        self.client = GnaniClient(
            settings.GNANI_API_KEY_ID,
            timeout=40.0,
        )
        self.url = "https://api.vachana.ai/stt/v3"

    async def extractTaskFromVoice(self, audio):
        sst = GnaniSTT(client=self.client)
        transcribe_output = await sst.transcribe(
            audio=audio, language=GuestLanguage.ENGLISH, filename="tts-output.wav"
        )
        print(transcribe_output)
        tasks = await self.provider.extract_tasks(transcript=transcribe_output.text)
        print(tasks)
