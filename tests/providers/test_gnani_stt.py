import httpx
import pytest
import respx

from app.providers.gnani.client import GnaniAPIError, GnaniClient
from app.providers.gnani.stt import GnaniSTT


@pytest.mark.asyncio
@respx.mock
async def test_transcribe_sends_correct_multipart_request():
    route = respx.post("https://api.vachana.ai/stt/v3").mock(
        return_value=httpx.Response(
            200,
            json={
                "success": True,
                "request_id": "test-request",
                "transcript": "hello from room 204",
                "model": "prisma-v2.5",
                "processing_time": 0.34,
                "end_to_end_latency": 0.37,
                "output": {"literal": "hello from room two zero four"},
            },
        )
    )

    audio = b"fake-audio-content"

    async with GnaniClient(api_key_id="test-key") as client:
        stt = GnaniSTT(client)

        response = await stt.transcribe(
            audio=audio,
            language="en-IN",
            filename="test.mp3",
        )

    request = route.calls.last.request
    request_body = request.content

    assert route.called
    assert request.headers["X-API-Key-ID"] == "test-key"
    assert "multipart/form-data" in request.headers["content-type"]
    assert b'name="language_code"' in request_body
    assert b"en-IN" in request_body
    assert b'name="audio_file"' in request_body
    assert b'filename="test.mp3"' in request_body
    assert audio in request_body

    assert response.text == "hello from room 204"
    assert response.literal_text == "hello from room two zero four"
    assert response.model == "prisma-v2.5"
    assert response.provider == "gnani"
    assert response.latency == 0.37


@pytest.mark.asyncio
@respx.mock
async def test_hinglish_uses_supported_hindi_code_for_stt():
    route = respx.post("https://api.vachana.ai/stt/v3").mock(
        return_value=httpx.Response(
            200,
            json={
                "success": True,
                "request_id": "test-request",
                "transcript": "Room service chahiye",
                "model": "prisma-v2.5",
                "processing_time": 0.34,
                "end_to_end_latency": 0.37,
                "output": {"literal": "Room service chahiye"},
            },
        )
    )

    async with GnaniClient(api_key_id="test-key") as client:
        stt = GnaniSTT(client)
        result = await stt.transcribe(
            audio=b"fake-audio-content",
            language="hi-en",
            filename="test.wav",
        )

    assert route.called
    assert b'name="language_code"\r\n\r\nhi-IN' in route.calls.last.request.content
    assert result.text == "Room service chahiye"


@pytest.mark.asyncio
@respx.mock
async def test_transcribe_rejects_malformed_response():
    respx.post("https://api.vachana.ai/stt/v3").mock(
        return_value=httpx.Response(
            200,
            json={
                "success": True,
                "request_id": "test-request",
            },
        )
    )

    async with GnaniClient(api_key_id="test-key") as client:
        stt = GnaniSTT(client)

        with pytest.raises(GnaniAPIError):
            await stt.transcribe(
                audio=b"fake-audio",
                language="en-IN",
                filename="test.wav",
            )
