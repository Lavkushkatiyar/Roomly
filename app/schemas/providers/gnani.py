from pydantic import BaseModel, ConfigDict


class GnaniSTTOutput(BaseModel):
    literal: str | None = None


class GnaniSTTResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    success: bool
    request_id: str
    transcript: str
    model: str
    processing_time: float | None = None
    end_to_end_latency: float | None = None
    output: GnaniSTTOutput | None = None


class TranscriptionResult(BaseModel):
    """Provider-independent transcription result for Roomly."""

    text: str
    literal_text: str | None = None
    provider: str = "gnani"
    model: str
    request_id: str
    processing_time: float | None = None
    latency: float | None = None


class SpeechGenerationResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    audio_data: bytes
    content_type: str
