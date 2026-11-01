import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.enums import RequestCategory, RequestPriority


class ProposedServiceRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    category: RequestCategory
    staff_summary: str = Field(min_length=1)
    priority: RequestPriority


class TaskExtractionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tasks: list[ProposedServiceRequest]


class TaskExtractionResponse(BaseModel):
    raw_input_id: uuid.UUID
    extraction: TaskExtractionResult
