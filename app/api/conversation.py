import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.conversation import ConversationCreate, ConversationResponse
from app.services.conversation_services import ConversationServices

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


@router.post(
    "/",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    conversation_data: ConversationCreate,
    db: Session = Depends(get_db),
):
    try:
        conversation = ConversationServices.create_conversation(
            db=db,
            room_id=conversation_data.room_id,
            guest_language=conversation_data.guest_language,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return conversation


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
)
def get_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    conversation = ConversationServices.get_active_conversation(
        db=db,
        conversation_id=conversation_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active conversation not found",
        )

    return conversation


@router.post(
    "/{conversation_id}/end",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
)
def end_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    conversation = ConversationServices.end_conversation(
        db=db,
        conversation_id=conversation_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active conversation not found",
        )

    return conversation
