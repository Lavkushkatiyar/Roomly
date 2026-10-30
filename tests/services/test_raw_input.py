import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models.enums import GuestLanguage
from app.db.models.hotel_room import HotelRoom
from app.db.models.raw_input import RawInput
from app.schemas.raw_input import RawInputCreate
from app.services.raw_input_services import RawInputServices


@pytest.fixture
def raw_input_data(db):
    room = HotelRoom(room_number="101")

    db.add(room)
    db.commit()
    db.refresh(room)

    return RawInputCreate(
        room_id=room.id,
        transcript="Test transcript",
        guest_language=GuestLanguage.ENGLISH,
    )


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    RawInput.metadata.create_all(bind=engine)

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


def test_create_raw_input_success(db, raw_input_data):
    result = RawInputServices.create_raw_input(db, raw_input_data)

    assert isinstance(result, RawInput)
    assert result.id is not None

    saved_result = db.scalar(select(RawInput).where(RawInput.id == result.id))

    assert saved_result is not None
    assert saved_result.id == result.id


def test_create_raw_input_commit_failure(db, raw_input_data, monkeypatch):
    def mock_commit():
        raise SQLAlchemyError("Commit failed")

    monkeypatch.setattr(db, "commit", mock_commit)

    with pytest.raises(SQLAlchemyError):
        RawInputServices.create_raw_input(db, raw_input_data)


def test_create_raw_input_add_failure(db, raw_input_data, monkeypatch):
    def mock_add(instance):
        raise SQLAlchemyError("Insert failed")

    monkeypatch.setattr(db, "add", mock_add)

    with pytest.raises(SQLAlchemyError):
        RawInputServices.create_raw_input(db, raw_input_data)

    result = db.scalar(select(RawInput))

    assert result is None


def test_get_raw_input_success(db, raw_input_data):
    created = RawInputServices.create_raw_input(db, raw_input_data)

    result = RawInputServices.get_raw_input(db, created.id)

    assert isinstance(result, RawInput)
    assert result.id == created.id


def test_get_raw_input_not_found(db):
    raw_input_id = uuid.uuid4()

    result = RawInputServices.get_raw_input(db, raw_input_id)

    assert result is None
