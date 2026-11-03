import asyncio
from pathlib import Path

from app.core.config import settings
from app.providers.gnani.client import GnaniClient
from app.providers.gnani.text_to_speech import (
    GnaniTTS,  # pyright: ignore[reportMissingImports]
)


async def main() -> None:
    async with GnaniClient(
        api_key_id=settings.GNANI_API_KEY_ID,
    ) as client:
        print(client)
        tts = GnaniTTS(client, settings.model)

        result = await tts.generate_voice(
            text="नमस्ते, आप कैसे हैं?",
            language_code="hi-IN",
            voice="Nalini",
        )

        output_path = Path("tts-output.wav")
        output_path.write_bytes(result.audio_data)

        print(f"Content type: {result.content_type}")
        print(f"Audio saved: {output_path.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())
