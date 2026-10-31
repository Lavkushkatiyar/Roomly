import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.enums import (
    RequestCategory,
    RequestPriority,
    RequestStatus,
)


class ServiceRequestCreate(BaseModel):
    raw_input_id: uuid.UUID
    category: RequestCategory
    staff_summary: str = Field(min_length=1)
    priority: RequestPriority = RequestPriority.MEDIUM


class ServiceRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    raw_input_id: uuid.UUID
    category: RequestCategory
    staff_summary: str
    priority: RequestPriority
    status: RequestStatus
    created_at: datetime
    updated_at: datetime
