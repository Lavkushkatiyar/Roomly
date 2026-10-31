from app.providers.gnani.client import GnaniClient
from app.schemas.providers.gnani import SpeechGenerationResult


class GnaniTTS:
    def __init__(self, client: GnaniClient, model: str) -> None:
        self.client = client
        self.model = model

    async def generateVoice(
        self, text: str, language_code: str, voice: str, speed: float = 1.0
    ) -> SpeechGenerationResult:
        payload = {
            "text": text,
            "voice": voice,
            "model": self.model,
            "language": language_code,
            "speed": speed,
            "audio_config": {
                "encoding": "linear_pcm",
                "container": "wav",
                "num_channels": 1,
                "sample_rate": 48000,
                "sample_width": 2,
            },
        }
        print(payload)
        response = await self.client.post_audio(
            "/api/v1/tts/inference",
            json=payload,
        )

        return SpeechGenerationResult(
            audio_data=response.content,
            content_type=response.headers.get("content-type", "audio/wav"),
            provider="gnani",
            model=self.model,
            request_id=response.headers.get("x-api-request-id"),
        )
