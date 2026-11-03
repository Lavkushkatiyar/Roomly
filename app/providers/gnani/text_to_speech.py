from app.providers.gnani.client import GnaniClient
from app.schemas.providers.gnani import SpeechGenerationResult


class GnaniTTS:
    def __init__(self, client: GnaniClient, model: str) -> None:
        self.client = client
        self.model = model

    async def generate_voice(
        self,
        text: str,
        language_code: str,
        voice: str = "Nalini",
        speed: float = 1.0,
    ) -> SpeechGenerationResult:
        if not text.strip():
            raise ValueError("Text cannot be empty.")

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

        response = await self.client.post_audio(
            "/api/v1/tts/inference",
            json=payload,
        )

        audio_data = response.content
        content_type = response.headers.get("content-type", "")

        if not audio_data:
            raise ValueError("Gnani TTS returned empty audio.")

        if not content_type.startswith("audio/"):
            raise ValueError(f"Unexpected audio content type: {content_type}")

        return SpeechGenerationResult(
            audio_data=audio_data,
            content_type=content_type,
        )
