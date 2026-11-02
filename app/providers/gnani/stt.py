import mimetypes

from pydantic import ValidationError

from app.providers.gnani.client import GnaniAPIError, GnaniClient
from app.schemas.providers.gnani import (
    GnaniSTTResponse,
    TranscriptionResult,
)


class GnaniSTT:
    ENDPOINT = "/stt/v3"

    def __init__(self, client: GnaniClient) -> None:
        self.client = client

    async def transcribe(
        self,
        audio: bytes,
        language: str,
        filename: str,
    ) -> TranscriptionResult:
        content_type, _ = mimetypes.guess_type(filename)
        print("we are coming till here")

        response = await self.client.post(
            self.ENDPOINT,
            data={"language_code": language},
            files={
                "audio_file": (
                    filename,
                    audio,
                    content_type or "application/octet-stream",
                ),
            },
        )

        try:
            provider_response = GnaniSTTResponse.model_validate(response)
        except ValidationError as exc:
            raise GnaniAPIError("Invalid response received from Gnani STT.") from exc

        if not provider_response.success:
            raise GnaniAPIError("Gnani transcription was unsuccessful.")

        return TranscriptionResult(
            text=provider_response.transcript,
            literal_text=(
                provider_response.output.literal if provider_response.output else None
            ),
            model=provider_response.model,
            request_id=provider_response.request_id,
            processing_time=provider_response.processing_time,
            latency=provider_response.end_to_end_latency,
        )
