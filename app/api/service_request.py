import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.models.enums import RequestStatus
from app.db.session import get_db
from app.schemas.service_request import (
    ServiceRequestCreate,
    ServiceRequestResponse,
)
from app.services.service_requests import ServiceRequestServices

router = APIRouter(
    prefix="/service-requests",
    tags=["Service Requests"],
)


@router.post(
    "/",
    response_model=ServiceRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_request(
    request_data: ServiceRequestCreate,
    db: Session = Depends(get_db),
):
    return ServiceRequestServices.create_service_request(db, request_data)


@router.get(
    "/",
    response_model=list[ServiceRequestResponse],
)
def list_requests(
    request_status: RequestStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return ServiceRequestServices.get_service_requests(
        db,
        status=request_status,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{request_id}",
    response_model=ServiceRequestResponse,
)
def retrieve_request(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    service_request = ServiceRequestServices.get_service_request(db, request_id)

    if service_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service request not found",
        )

    return service_request


@router.patch(
    "/{request_id}/status",
    response_model=ServiceRequestResponse,
)
def update_request_status(
    request_id: uuid.UUID,
    new_status: RequestStatus,
    db: Session = Depends(get_db),
):
    service_request = ServiceRequestServices.update_service_request_status(
        db,
        request_id,
        new_status,
    )

    if service_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service request not found",
        )

    return service_request
