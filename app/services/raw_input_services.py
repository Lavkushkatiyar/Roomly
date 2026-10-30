import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.raw_input import RawInput
from app.schemas.raw_input import RawInputCreate


class RawInputServices:
    @staticmethod
    def create_raw_input(
        db: Session,
        raw_input_data: RawInputCreate,
    ) -> RawInput:
        raw_input = RawInput(
            **raw_input_data.model_dump(),
        )

        try:
            db.add(raw_input)
            db.commit()
            db.refresh(raw_input)
        except SQLAlchemyError:
            db.rollback()
            raise

        return raw_input

    @staticmethod
    def get_raw_input(
        db: Session,
        raw_input_id: uuid.UUID,
    ) -> RawInput | None:
        statement = select(RawInput).where(RawInput.id == raw_input_id)

        return db.scalar(statement)
