import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.enums import (
    GuestLanguage,
    RequestCategory,
    RequestPriority,
    RequestStatus,
)
from app.db.models.hotel_room import HotelRoom
from app.db.models.raw_input import RawInput
from app.db.models.service_requests import ServiceRequest
from app.schemas.service_request import ServiceRequestCreate
from app.services.service_requests import ServiceRequestServices


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    try:
        with Session(engine) as session:
            yield session
    finally:
        engine.dispose()


@pytest.fixture
def raw_input_id(db):
    room = HotelRoom(room_number="101")
    db.add(room)
    db.flush()

    raw_input = RawInput(
        room_id=room.id,
        transcript="The air conditioner is not working.",
        guest_language=GuestLanguage.ENGLISH,
    )
    db.add(raw_input)
    db.commit()
    db.refresh(raw_input)

    return raw_input.id


def make_request_data(raw_input_id, *, summary="AC is not working"):
    return ServiceRequestCreate(
        raw_input_id=raw_input_id,
        category=RequestCategory.MAINTENANCE,
        staff_summary=summary,
        priority=RequestPriority.HIGH,
    )


def test_create_service_request(db, raw_input_id):
    result = ServiceRequestServices.create_service_request(
        db,
        make_request_data(raw_input_id),
    )

    assert isinstance(result, ServiceRequest)
    assert result.id is not None
    assert result.raw_input_id == raw_input_id
    assert result.category == RequestCategory.MAINTENANCE
    assert result.staff_summary == "AC is not working"
    assert result.priority == RequestPriority.HIGH
    assert result.status == RequestStatus.OPEN


def test_get_service_request(db, raw_input_id):
    created = ServiceRequestServices.create_service_request(
        db,
        make_request_data(raw_input_id),
    )

    result = ServiceRequestServices.get_service_request(db, created.id)

    assert result is not None
    assert result.id == created.id


def test_get_service_request_not_found(db):
    result = ServiceRequestServices.get_service_request(db, uuid.uuid4())

    assert result is None


def test_get_service_requests_returns_newest_first(db, raw_input_id):
    older = ServiceRequestServices.create_service_request(
        db,
        make_request_data(raw_input_id, summary="Older request"),
    )
    newer = ServiceRequestServices.create_service_request(
        db,
        make_request_data(raw_input_id, summary="Newer request"),
    )

    older.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    newer.created_at = datetime(2026, 1, 2, tzinfo=UTC)
    db.commit()

    result = ServiceRequestServices.get_service_requests(db)

    assert [request.id for request in result] == [newer.id, older.id]


def test_get_service_requests_filters_by_status(db, raw_input_id):
    open_request = ServiceRequestServices.create_service_request(
        db,
        make_request_data(raw_input_id, summary="Open request"),
    )
    resolved_request = ServiceRequestServices.create_service_request(
        db,
        make_request_data(raw_input_id, summary="Resolved request"),
    )
    resolved_request.status = RequestStatus.RESOLVED
    db.commit()

    result = ServiceRequestServices.get_service_requests(
        db,
        status=RequestStatus.OPEN,
    )

    assert [request.id for request in result] == [open_request.id]


def test_get_service_requests_applies_limit_and_offset(db, raw_input_id):
    requests = [
        ServiceRequestServices.create_service_request(
            db,
            make_request_data(raw_input_id, summary=f"Request {index}"),
        )
        for index in range(3)
    ]
    for index, request in enumerate(requests):
        request.created_at = datetime(2026, 1, index + 1, tzinfo=UTC)
    db.commit()

    result = ServiceRequestServices.get_service_requests(
        db,
        limit=1,
        offset=1,
    )

    assert [request.id for request in result] == [requests[1].id]


def test_update_service_request_status(db, raw_input_id):
    created = ServiceRequestServices.create_service_request(
        db,
        make_request_data(raw_input_id),
    )

    result = ServiceRequestServices.update_service_request_status(
        db,
        created.id,
        RequestStatus.IN_PROGRESS,
    )

    assert result is not None
    assert result.id == created.id
    assert result.status == RequestStatus.IN_PROGRESS


def test_update_service_request_status_not_found(db):
    result = ServiceRequestServices.update_service_request_status(
        db,
        uuid.uuid4(),
        RequestStatus.IN_PROGRESS,
    )

    assert result is None
