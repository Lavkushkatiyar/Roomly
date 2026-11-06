import json
import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.conversation import Conversation
from app.db.models.conversation_message import ConversationMessage
from app.db.models.enums import ConversationStatus, GuestLanguage, MessageRole
from app.db.models.hotel_room import HotelRoom
from app.db.models.raw_input import RawInput
from app.schemas.task_extraction import ProposedServiceRequest

PENDING_TASKS_MARKER = "\n[roomly-pending-tasks:"
CLOSING_UTTERANCES = {
    "all done",
    "bye",
    "done thanks",
    "done thank you",
    "goodbye",
    "i am done",
    "i am done thanks",
    "i am done thank you",
    "it is done",
    "it is done thanks",
    "it is done thank you",
    "im done",
    "im done thanks",
    "im done thank you",
    "no more",
    "no more thanks",
    "no more thank you",
    "nothing else",
    "nothing else thanks",
    "nothing else thank you",
    "thank you",
    "thank you that is everything",
    "thank you that is it",
    "thank you that is all",
    "thank you we are done",
    "thanks",
    "thanks that is all",
    "thanks that is everything",
    "thanks that is it",
    "thanks we are done",
    "that is all",
    "that is all thank you",
    "that is all thanks",
    "that is everything",
    "that is everything thank you",
    "that is everything thanks",
    "that is it",
    "that is it thank you",
    "that is it thanks",
    "we are done",
    "we are done thanks",
    "we are done thank you",
    "we are finished",
    "we are finished thanks",
    "we are finished thank you",
}


def is_conversation_closing_utterance(transcript: str) -> bool:
    normalized = transcript.lower()
    normalized = re.sub(r"\bthat's\b", "that is", normalized)
    normalized = re.sub(r"\bwe're\b", "we are", normalized)
    normalized = re.sub(r"\bi'm\b", "i am", normalized)
    normalized = re.sub(r"\bit's\b", "it is", normalized)
    normalized = re.sub(r"[^\w\s]", "", normalized)
    normalized = " ".join(normalized.split())
    return normalized in CLOSING_UTTERANCES


class ConversationServices:
    @staticmethod
    def create_conversation(
        db: Session,
        room_id: uuid.UUID,
        guest_language: GuestLanguage,
    ) -> Conversation:
        room = db.get(HotelRoom, room_id)

        if room is None or not room.is_active:
            raise ValueError("Invalid or inactive hotel room")

        conversation = Conversation(
            room_id=room_id,
            guest_language=guest_language,
            status=ConversationStatus.ACTIVE,
        )

        try:
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        except SQLAlchemyError:
            db.rollback()
            raise

        return conversation

    @staticmethod
    def get_active_conversation(
        db: Session,
        conversation_id: uuid.UUID,
    ) -> Conversation | None:
        statement = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.status == ConversationStatus.ACTIVE,
        )

        return db.scalar(statement)

    @staticmethod
    def get_all_conversations(
        db: Session,
    ):
        statement = select(Conversation)
        return list(db.scalars(statement).all())

    @staticmethod
    def save_message(
        db: Session,
        conversation_id: uuid.UUID,
        role: MessageRole,
        content: str,
    ) -> ConversationMessage:
        conversation = ConversationServices.get_active_conversation(
            db,
            conversation_id,
        )

        if conversation is None:
            raise ValueError("Conversation does not exist or has ended")

        message = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content.strip(),
        )

        try:
            db.add(message)
            db.commit()
            db.refresh(message)
        except SQLAlchemyError:
            db.rollback()
            raise

        return message

    @staticmethod
    def save_turn_message(
        db: Session,
        conversation_id: uuid.UUID,
        content: str,
        pending_tasks: list[ProposedServiceRequest],
        pending_raw_input_id: uuid.UUID | None,
    ) -> ConversationMessage:
        serialized_tasks = json.dumps(
            {
                "raw_input_id": (
                    str(pending_raw_input_id)
                    if pending_raw_input_id is not None
                    else None
                ),
                "tasks": [task.model_dump(mode="json") for task in pending_tasks],
            },
            separators=(",", ":"),
        )
        stored_content = f"{content.strip()}{PENDING_TASKS_MARKER}{serialized_tasks}]"

        return ConversationServices.save_message(
            db=db,
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=stored_content,
        )

    @staticmethod
    def get_pending_proposal(
        db: Session,
        conversation_id: uuid.UUID,
    ) -> tuple[uuid.UUID | None, list[ProposedServiceRequest]]:
        statement = (
            select(ConversationMessage.content)
            .where(
                ConversationMessage.conversation_id == conversation_id,
                ConversationMessage.role == MessageRole.ASSISTANT,
            )
            .order_by(ConversationMessage.created_at.desc())
            .limit(1)
        )
        content = db.scalar(statement)

        if content is None or PENDING_TASKS_MARKER not in content:
            return None, []

        serialized_tasks = content.rsplit(PENDING_TASKS_MARKER, 1)[1]
        try:
            proposal_data = json.loads(serialized_tasks.removesuffix("]"))
            if isinstance(proposal_data, list):
                raw_input_id = None
                task_data = proposal_data
            else:
                raw_input_id = (
                    uuid.UUID(proposal_data["raw_input_id"])
                    if proposal_data["raw_input_id"] is not None
                    else None
                )
                task_data = proposal_data["tasks"]

            tasks = [ProposedServiceRequest.model_validate(task) for task in task_data]
            return raw_input_id, tasks
        except (KeyError, json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ValueError("Stored conversation proposal is invalid.") from exc

    @staticmethod
    def get_pending_tasks(
        db: Session,
        conversation_id: uuid.UUID,
    ) -> list[ProposedServiceRequest]:
        _, tasks = ConversationServices.get_pending_proposal(
            db=db,
            conversation_id=conversation_id,
        )
        return tasks

    @staticmethod
    def _validate_conversation(
        db: Session,
        conversation_id: uuid.UUID,
    ) -> None:
        conversation = ConversationServices.get_active_conversation(
            db=db,
            conversation_id=conversation_id,
        )

        if conversation is None:
            raise ValueError("Active conversation not found.")

    @staticmethod
    def _get_guest_messages(
        db: Session,
        conversation_id: uuid.UUID,
    ) -> list[dict]:
        guest_messages = db.execute(
            select(RawInput.transcript, RawInput.created_at).where(
                RawInput.conversation_id == conversation_id
            )
        ).all()

        return [
            {
                "role": MessageRole.GUEST.value,
                "content": content,
                "created_at": created_at,
            }
            for content, created_at in guest_messages
        ]

    @staticmethod
    def _get_assistant_messages(
        db: Session,
        conversation_id: uuid.UUID,
    ) -> list[dict]:
        assistant_messages = db.execute(
            select(ConversationMessage.content, ConversationMessage.created_at).where(
                ConversationMessage.conversation_id == conversation_id,
                ConversationMessage.role == MessageRole.ASSISTANT,
            )
        ).all()

        return [
            {
                "role": MessageRole.ASSISTANT.value,
                "content": content,
                "created_at": created_at,
            }
            for content, created_at in assistant_messages
        ]

    @staticmethod
    def get_conversation_context(
        db: Session,
        conversation_id: uuid.UUID,
        limit: int = 10,
    ) -> list[dict[str, str]]:
        ConversationServices._validate_conversation(
            db=db,
            conversation_id=conversation_id,
        )

        guest_messages = ConversationServices._get_guest_messages(
            db=db,
            conversation_id=conversation_id,
        )

        assistant_messages = ConversationServices._get_assistant_messages(
            db=db,
            conversation_id=conversation_id,
        )

        messages = guest_messages + assistant_messages
        messages.sort(key=lambda message: message["created_at"])

        context = []
        for message in messages[-limit:]:
            content = message["content"]
            if PENDING_TASKS_MARKER in content:
                assistant_text, serialized_tasks = content.rsplit(
                    PENDING_TASKS_MARKER,
                    1,
                )
                try:
                    proposal_data = json.loads(serialized_tasks.removesuffix("]"))
                    task_data = (
                        proposal_data
                        if isinstance(proposal_data, list)
                        else proposal_data["tasks"]
                    )
                except (KeyError, json.JSONDecodeError, TypeError) as exc:
                    raise ValueError(
                        "Stored conversation proposal is invalid."
                    ) from exc
                content = (
                    f"{assistant_text}\n"
                    "Pending service requests (internal context, not yet "
                    f"submitted): {json.dumps(task_data, separators=(',', ':'))}"
                )
            context.append({"role": message["role"], "content": content})

        return context

    @staticmethod
    def end_conversation(
        db: Session,
        conversation_id: uuid.UUID,
    ) -> Conversation | None:
        conversation = ConversationServices.get_active_conversation(
            db,
            conversation_id,
        )

        if conversation is None:
            return None

        conversation.status = ConversationStatus.ENDED
        conversation.ended_at = datetime.now(UTC)

        try:
            db.commit()
            db.refresh(conversation)
        except SQLAlchemyError:
            db.rollback()
            raise

        return conversation
