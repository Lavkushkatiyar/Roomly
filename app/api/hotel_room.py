from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.hotel_room import HotelRoomCreate, HotelRoomResponse
from app.services.hotel_room_services import HotelRoomServices

router = APIRouter(prefix="/hotel_room", tags=["Hotel_room"])


@router.get("/", response_model=list[HotelRoomResponse], status_code=status.HTTP_200_OK)
def get_all_rooms(db: Session = Depends(get_db)):
    return HotelRoomServices.get_all_rooms(db)


@router.get(
    "/{room_number}",
    response_model=list[HotelRoomResponse],
    status_code=status.HTTP_200_OK,
)
def get_room_by_number(room_number: str, db: Session = Depends(get_db)):
    return HotelRoomServices.get_hotel_room_by_number(db=db, room_number=room_number)


@router.post("/", response_model=HotelRoomCreate, status_code=status.HTTP_201_CREATED)
def add_room(room_number: str, db: Session = Depends(get_db)):
    return HotelRoomServices.create_hotel_room(db=db, room_number=room_number)
