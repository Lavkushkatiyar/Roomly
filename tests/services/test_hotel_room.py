import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import HotelRoom
from app.services.hotel_room_services import HotelRoomServices as crud


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    HotelRoom.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        engine.dispose()


# 1. ADD IN DB


def test_add_in_db(db):
    room = HotelRoom(room_number="101")

    crud.add_in_db(db, room)

    saved_room = db.query(HotelRoom).filter_by(room_number="101").first()

    assert saved_room is not None
    assert saved_room.room_number == "101"


# 2. CREATE HOTEL ROOM


def test_create_hotel_room(db):
    room = crud.create_hotel_room(db, "101")

    assert room is not None
    assert room.room_number == "101"

    saved_room = db.query(HotelRoom).filter_by(room_number="101").first()

    assert saved_room is not None


def test_create_duplicate_hotel_room(db):
    crud.create_hotel_room(db, "101")

    with pytest.raises(ValueError, match="Room already exists"):
        crud.create_hotel_room(db, "101")


def test_create_room_integrity_error(db, monkeypatch):
    def mock_add_in_db(*args, **kwargs):
        raise IntegrityError(
            "INSERT",
            {},
            Exception("Unique constraint violation"),
        )

    monkeypatch.setattr(crud, "add_in_db", mock_add_in_db)

    with pytest.raises(ValueError, match="Room number already exists"):
        crud.create_hotel_room(db, "101")


def test_create_room_database_error(db, monkeypatch):
    def mock_add_in_db(*args, **kwargs):
        raise SQLAlchemyError("Database unavailable")

    monkeypatch.setattr(crud, "add_in_db", mock_add_in_db)

    with pytest.raises(RuntimeError, match="Failed to create hotel room"):
        crud.create_hotel_room(db, "101")


# 3. GET ALL ROOMS


def test_get_all_rooms(db):
    crud.create_hotel_room(db, "101")
    crud.create_hotel_room(db, "102")
    crud.create_hotel_room(db, "103")

    rooms = crud.get_all_rooms(db)

    assert len(rooms) == 3
    assert {room.room_number for room in rooms} == {
        "101",
        "102",
        "103",
    }


def test_get_all_rooms_empty(db):
    rooms = crud.get_all_rooms(db)

    assert rooms == []


# 4. GET ROOM BY NUMBER


def test_get_hotel_room_by_number(db):
    crud.create_hotel_room(db, "101")

    room = crud.get_hotel_room_by_number(db, "101")

    assert room is not None
    assert room.room_number == "101"


def test_get_hotel_room_by_number_not_found(db):
    room = crud.get_hotel_room_by_number(db, "999")

    assert room is None
