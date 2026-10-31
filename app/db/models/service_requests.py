import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.enums import RequestCategory, RequestPriority, RequestStatus


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    raw_input_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("raw_inputs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    category: Mapped[RequestCategory] = mapped_column(
        Enum(RequestCategory, name="service_request_category"),
        nullable=False,
    )

    staff_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    priority: Mapped[RequestPriority] = mapped_column(
        Enum(RequestPriority, name="service_request_priority"),
        default=RequestPriority.MEDIUM,
        nullable=False,
    )

    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, name="service_request_status"),
        default=RequestStatus.OPEN,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
