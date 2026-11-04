from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models.enums import (
    GuestLanguage,
    RequestCategory,
    RequestPriority,
    RequestStatus,
)
from app.db.models.hotel_room import HotelRoom
from app.db.models.raw_input import RawInput
from app.schemas.task_extraction import ProposedServiceRequest
from app.services.service_requests import ServiceRequestServices


def test_create_service_requests():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        room = HotelRoom(room_number="205")
        db.add(room)
        db.commit()
        db.refresh(room)

        raw_input = RawInput(
            room_id=room.id,
            transcript="Please send water and an extra pillow.",
            guest_language=GuestLanguage.ENGLISH,
            # Add any other required RawInput fields here.
        )

        db.add(raw_input)
        db.commit()
        db.refresh(raw_input)

        raw_input_id = raw_input.id
        proposed_requests = [
            ProposedServiceRequest(
                category=RequestCategory.HOUSEKEEPING,
                staff_summary="Send two bottles of mineral water.",
                priority=RequestPriority.LOW,
            ),
            ProposedServiceRequest(
                category=RequestCategory.HOUSEKEEPING,
                staff_summary="Send an extra pillow.",
                priority=RequestPriority.MEDIUM,
            ),
        ]

        created_requests = ServiceRequestServices.create_service_requests(
            db=db,
            raw_input_id=raw_input_id,
            requests=proposed_requests,
        )

        assert len(created_requests) == 2

        assert all(request.raw_input_id == raw_input.id for request in created_requests)

        assert created_requests[0].staff_summary == (
            "Send two bottles of mineral water."
        )
        assert created_requests[1].staff_summary == "Send an extra pillow."

        assert all(request.id is not None for request in created_requests)

        assert all(request.status == RequestStatus.OPEN for request in created_requests)

    Base.metadata.drop_all(bind=engine)
    engine.dispose()
