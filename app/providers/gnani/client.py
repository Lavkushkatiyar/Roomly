import logging
from collections.abc import Mapping
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class GnaniAPIError(Exception):
    """Raised when Gnani returns an unsuccessful or invalid response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
    ) -> None:
        self.status_code = status_code
        super().__init__(message)


class GnaniClient:
    BASE_URL = "https://api.vachana.ai"

    def __init__(
        self,
        api_key_id: str,
        *,
        timeout: float = 30.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not api_key_id:
            raise ValueError("Gnani API key ID is required.")

        self._http = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"X-API-Key-ID": api_key_id},
            timeout=httpx.Timeout(timeout),
            transport=transport,
        )

    async def post(
        self,
        path: str,
        *,
        data: Mapping[str, str],
        files: Mapping[str, tuple[str, bytes, str]],
    ) -> dict[str, Any]:
        try:
            response = await self._http.post(
                path,
                data=data,
                files=files,
            )
            response.raise_for_status()
            payload = response.json()

        except httpx.HTTPStatusError as exc:
            logger.error(
                "Gnani API error: status=%s, response=%s",
                exc.response.status_code,
                exc.response.text,
            )
            raise GnaniAPIError(
                "Gnani rejected the request.",
                status_code=exc.response.status_code,
            ) from exc

        except httpx.RequestError as exc:
            raise GnaniAPIError("Unable to reach the Gnani API.") from exc

        except ValueError as exc:
            raise GnaniAPIError("Gnani returned an invalid JSON response.") from exc

        if not isinstance(payload, dict):
            raise GnaniAPIError("Gnani returned an unexpected response.")

        return payload

    async def post_audio(
        self,
        path: str,
        *,
        json: Mapping[str, Any],
    ) -> httpx.Response:
        response = await self._http.post(path, json=json)

        logger.info("Gnani TTS status: %s", response.status_code)
        logger.info("Gnani TTS response: %s", response.text)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise GnaniAPIError(
                "Gnani rejected the TTS request.",
                status_code=exc.response.status_code,
            ) from exc

        content_type = response.headers.get("content-type", "")

        if not content_type.startswith("audio/") or not response.content:
            raise GnaniAPIError(
                "Gnani returned an invalid audio response.",
                status_code=response.status_code,
            )

        return response

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "GnaniClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()
