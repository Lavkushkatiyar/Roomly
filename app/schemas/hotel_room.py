from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class HotelRoomCreate(BaseModel):
    room_number: str = Field(
        min_length=1,
        max_length=10,
    )


class HotelRoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    room_number: str
    is_active: bool
