import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.enums import RequestStatus
from app.db.models.service_requests import ServiceRequest
from app.schemas.service_request import ServiceRequestCreate
from app.schemas.task_extraction import ProposedServiceRequest


class ServiceRequestServices:
    @staticmethod
    def create_service_request(
        db: Session,
        request_data: ServiceRequestCreate,
    ) -> ServiceRequest:
        service_request = ServiceRequest(
            **request_data.model_dump(),
        )

        db.add(service_request)
        db.commit()
        db.refresh(service_request)

        return service_request

    @staticmethod
    def get_service_request(
        db: Session,
        request_id: uuid.UUID,
    ) -> ServiceRequest | None:
        statement = select(ServiceRequest).where(ServiceRequest.id == request_id)

        return db.scalar(statement)

    @staticmethod
    def get_service_requests(
        db: Session,
        *,
        status: RequestStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ServiceRequest]:
        statement = select(ServiceRequest)

        if status is not None:
            statement = statement.where(ServiceRequest.status == status)

        statement = (
            statement.order_by(ServiceRequest.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        return list(db.scalars(statement).all())

    @staticmethod
    def update_service_request_status(
        db: Session,
        request_id: uuid.UUID,
        new_status: RequestStatus,
    ) -> ServiceRequest | None:
        service_request = ServiceRequestServices.get_service_request(db, request_id)

        if service_request is not None:
            service_request.status = new_status
            db.commit()
            db.refresh(service_request)

        return service_request

    @staticmethod
    def create_service_requests(
        db: Session,
        raw_input_id: uuid.UUID,
        requests: list[ProposedServiceRequest],
        *,
        commit: bool = True,
    ) -> list[ServiceRequest]:
        service_requests = [
            ServiceRequest(raw_input_id=raw_input_id, **request.model_dump())
            for request in requests
        ]

        try:
            db.add_all(service_requests)
            if commit:
                db.commit()

                for service_request in service_requests:
                    db.refresh(service_request)
        except SQLAlchemyError:
            db.rollback()
            raise

        return service_requests
