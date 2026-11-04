from pydantic import BaseModel, ConfigDict


class VoiceConfirmationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transcript: str
    confirmation: str
