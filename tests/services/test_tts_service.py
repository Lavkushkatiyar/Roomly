from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.assistant import AssistantResponse
from app.schemas.providers.gnani import SpeechGenerationResult
from app.services.tts_service import TTSService


@pytest.mark.parametrize(
    ("language", "expected_voice"),
    [
        ("en-IN", "Kaveri"),
        ("hi-IN", "Nalini"),
        ("hi-en", "Poorvi"),
        ("ta-IN", "Asmita"),
        ("te-IN", "Suhana"),
        ("kn-IN", "Saanvi"),
        ("ml-IN", "Reshma"),
        ("mr-IN", "Zahira"),
        ("bn-IN", "Kirra"),
        ("gu-IN", "Falak"),
        ("pa-IN", "Mehuli"),
    ],
)
@pytest.mark.asyncio
async def test_generate_speech_uses_voice_for_response_language(
    language,
    expected_voice,
):
    provider = MagicMock()
    provider.generate_voice = AsyncMock(
        return_value=SpeechGenerationResult(
            audio_data=b"audio",
            content_type="audio/wav",
        )
    )
    assistant_response = AssistantResponse(
        text="Welcome.",
        language=language,
    )

    result = await TTSService(provider).generate_speech(assistant_response)

    provider.generate_voice.assert_awaited_once_with(
        text="Welcome.",
        language_code=language,
        voice=expected_voice,
    )
    assert result.audio_data == b"audio"


@pytest.mark.asyncio
async def test_generate_speech_uses_default_voice_for_unmapped_language():
    provider = MagicMock()
    provider.generate_voice = AsyncMock(
        return_value=SpeechGenerationResult(
            audio_data=b"audio",
            content_type="audio/wav",
        )
    )

    await TTSService(provider).generate_speech(
        AssistantResponse(text="Welcome.", language="fr-FR")
    )

    provider.generate_voice.assert_awaited_once_with(
        text="Welcome.",
        language_code="fr-FR",
        voice="Avinash",
    )
