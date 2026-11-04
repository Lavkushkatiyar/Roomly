import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.task_extraction import TaskExtractionResponse
from app.services.raw_input_services import RawInputServices
from app.services.task_extraction import TaskExtractionServices

router = APIRouter(
    prefix="/task-extraction",
    tags=["Task Extraction"],
)


@router.post("/{raw_input_id}", response_model=TaskExtractionResponse)
async def extract_tasks(raw_input_id: uuid.UUID, db: Session = Depends(get_db)):
    raw_input = RawInputServices.get_raw_input(db, raw_input_id=raw_input_id)
    if raw_input is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="raw_input not found "
        )
    extraction_service = TaskExtractionServices()
    result = await extraction_service.extract_tasks_from_text(raw_input.transcript)

    return TaskExtractionResponse(raw_input_id=raw_input_id, extraction=result)
