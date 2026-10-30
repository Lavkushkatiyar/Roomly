from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import HotelRoom


class HotelRoomServices:
    @staticmethod
    def add_in_db(db: Session, record) -> None:
        db.add(record)
        db.commit()
        db.refresh(record)

    @staticmethod
    def create_hotel_room(db: Session, room_number: str) -> HotelRoom:
        room = db.query(HotelRoom).filter(HotelRoom.room_number == room_number).first()

        if room:
            raise ValueError("Room already exists.")

        room = HotelRoom(room_number=room_number)

        try:
            HotelRoomServices.add_in_db(db=db, record=room)
        except IntegrityError as error:
            db.rollback()
            raise ValueError("Room number already exists.") from error
        except SQLAlchemyError as error:
            db.rollback()
            raise RuntimeError("Failed to create hotel room.") from error

        return room

    @staticmethod
    def get_all_rooms(db: Session) -> list[HotelRoom]:
        return db.query(HotelRoom).all()

    @staticmethod
    def get_hotel_room_by_number(
        db: Session,
        room_number: str,
    ) -> HotelRoom | None:
        statement = select(HotelRoom).where(HotelRoom.room_number == room_number)

        return db.scalar(statement)
