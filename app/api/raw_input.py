import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.raw_input import RawInputCreate, RawInputResponse
from app.services.raw_input_services import RawInputServices

router = APIRouter(prefix="/raw_input", tags=["Raw_Inputs"])


@router.post("/", response_model=RawInputResponse, status_code=status.HTTP_201_CREATED)
def add_raw_input(input_data: RawInputCreate, db: Session = Depends(get_db)):
    raw_input_create = RawInputServices.create_raw_input(
        db=db, raw_input_data=input_data
    )

    if raw_input_create is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raw input not found",
        )

    return raw_input_create


@router.get(
    "/{raw_input_id}",
    response_model=RawInputResponse,
    status_code=status.HTTP_200_OK,
)
def get_raw_input_endpoint(
    raw_input_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    raw_input = RawInputServices.get_raw_input(db, raw_input_id)

    if raw_input is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raw input not found",
        )

    return raw_input
