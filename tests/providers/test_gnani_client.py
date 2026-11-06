import asyncio

import httpx
import pytest
import respx

from app.providers.gnani.client import GnaniAPIError, GnaniClient


def test_post_sends_authenticated_multipart_request():
    captured_requests = []

    async def handler(request):
        captured_requests.append(request)
        return httpx.Response(200, json={"success": True})

    async def run():
        async with GnaniClient(
            "test-key",
            transport=httpx.MockTransport(handler),
        ) as client:
            return await client.post(
                "/v1/stt",
                data={"language": "en-IN"},
                files={"file": ("sample.wav", b"audio data", "audio/wav")},
            )

    result = asyncio.run(run())

    assert result == {"success": True}
    assert len(captured_requests) == 1
    request = captured_requests[0]
    assert request.method == "POST"
    assert request.url.path == "/v1/stt"
    assert request.headers["X-API-Key-ID"] == "test-key"
    assert b"en-IN" in request.content
    assert b"sample.wav" in request.content
    assert b"audio data" in request.content


@pytest.mark.asyncio
async def test_requests_to_gnani_are_serialized():
    first_request_started = asyncio.Event()
    release_first_request = asyncio.Event()
    active_requests = 0
    max_active_requests = 0
    request_count = 0

    async def handler(request):
        nonlocal active_requests, max_active_requests, request_count
        request_count += 1
        active_requests += 1
        max_active_requests = max(max_active_requests, active_requests)
        if request_count == 1:
            first_request_started.set()
            await release_first_request.wait()
        active_requests -= 1
        return httpx.Response(200, json={"success": True})

    async with GnaniClient(
        "test-key",
        transport=httpx.MockTransport(handler),
    ) as client:
        first = asyncio.create_task(client.post("/first", data={}, files={}))
        await first_request_started.wait()
        second = asyncio.create_task(client.post("/second", data={}, files={}))

        await asyncio.sleep(0)
        assert request_count == 1

        release_first_request.set()
        await asyncio.gather(first, second)

    assert max_active_requests == 1
    assert request_count == 2


@pytest.mark.asyncio
async def test_post_retries_rate_limited_request():
    request_count = 0

    async def handler(request):
        nonlocal request_count
        request_count += 1
        if request_count == 1:
            return httpx.Response(
                429,
                headers={"Retry-After": "0"},
                json={"detail": "Only 1 active request is allowed at a time."},
            )
        return httpx.Response(200, json={"success": True})

    async with GnaniClient(
        "test-key",
        transport=httpx.MockTransport(handler),
    ) as client:
        response = await client.post("/stt/v3", data={}, files={})

    assert response == {"success": True}
    assert request_count == 2


@pytest.mark.asyncio
async def test_post_retries_gateway_timeout(monkeypatch):
    request_count = 0
    monkeypatch.setattr(GnaniClient, "GATEWAY_RETRY_DELAYS", (0, 0))

    async def handler(request):
        nonlocal request_count
        request_count += 1
        if request_count == 1:
            return httpx.Response(504, request=request)
        return httpx.Response(200, json={"success": True})

    async with GnaniClient(
        "test-key",
        transport=httpx.MockTransport(handler),
    ) as client:
        response = await client.post("/stt/v3", data={}, files={})

    assert response == {"success": True}
    assert request_count == 2


@pytest.mark.asyncio
async def test_post_stops_retrying_after_gateway_retry_limit(monkeypatch):
    request_count = 0
    monkeypatch.setattr(GnaniClient, "GATEWAY_RETRY_DELAYS", (0, 0))

    async def handler(request):
        nonlocal request_count
        request_count += 1
        return httpx.Response(504, request=request)

    async with GnaniClient(
        "test-key",
        transport=httpx.MockTransport(handler),
    ) as client:
        with pytest.raises(GnaniAPIError) as error:
            await client.post("/stt/v3", data={}, files={})

    assert error.value.status_code == 504
    assert request_count == 3


def test_post_raises_api_error_for_http_status():
    async def handler(request):
        return httpx.Response(401, request=request)

    async def run():
        async with GnaniClient(
            "test-key",
            transport=httpx.MockTransport(handler),
        ) as client:
            with pytest.raises(GnaniAPIError) as error:
                await client.post("/v1/stt", data={}, files={})

        assert error.value.status_code == 401
        assert isinstance(error.value.__cause__, httpx.HTTPStatusError)

    asyncio.run(run())


def test_post_raises_api_error_for_connection_failure():
    async def handler(request):
        raise httpx.ConnectError("Connection failed", request=request)

    async def run():
        async with GnaniClient(
            "test-key",
            transport=httpx.MockTransport(handler),
        ) as client:
            with pytest.raises(GnaniAPIError) as error:
                await client.post("/v1/stt", data={}, files={})

        assert error.value.status_code is None
        assert isinstance(error.value.__cause__, httpx.RequestError)

    asyncio.run(run())


def test_post_raises_api_error_for_invalid_json():
    async def handler(request):
        return httpx.Response(200, content=b"not json")

    async def run():
        async with GnaniClient(
            "test-key",
            transport=httpx.MockTransport(handler),
        ) as client:
            with pytest.raises(GnaniAPIError, match="invalid JSON"):
                await client.post("/v1/stt", data={}, files={})

    asyncio.run(run())


def test_post_raises_api_error_for_non_object_json():
    async def handler(request):
        return httpx.Response(200, json=["unexpected"])

    async def run():
        async with GnaniClient(
            "test-key",
            transport=httpx.MockTransport(handler),
        ) as client:
            with pytest.raises(GnaniAPIError, match="unexpected response"):
                await client.post("/v1/stt", data={}, files={})

    asyncio.run(run())


def test_client_requires_api_key_id():
    with pytest.raises(ValueError, match="API key ID is required"):
        GnaniClient("")


@pytest.mark.asyncio
@respx.mock
async def test_client_sends_authenticated_request():
    route = respx.post("https://api.vachana.ai/test").mock(
        return_value=httpx.Response(
            200,
            json={"success": True},
        )
    )

    async with GnaniClient(api_key_id="test-key") as client:
        response = await client.post(
            "/test",
            data={},
            files={},
        )

    assert route.called
    assert route.calls.last.request.headers["X-API-Key-ID"] == "test-key"
    assert response == {"success": True}


@pytest.mark.asyncio
@respx.mock
async def test_client_raises_error_for_http_failure():
    respx.post("https://api.vachana.ai/test").mock(return_value=httpx.Response(401))

    async with GnaniClient(api_key_id="test-key") as client:
        with pytest.raises(GnaniAPIError) as exc_info:
            await client.post(
                "/test",
                data={},
                files={},
            )

    assert exc_info.value.status_code == 401
