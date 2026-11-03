from pydantic import BaseModel, ConfigDict, Field


class AssistantResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    text: str = Field(min_length=1)
    language: str = Field(min_length=2)
