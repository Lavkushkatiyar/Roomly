import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.db.models.enums import (
    ConversationStatus,
    GuestLanguage,
    MessageRole,
    RequestCategory,
    RequestPriority,
)
from app.schemas.task_extraction import ProposedServiceRequest
from app.services.conversation_services import ConversationServices


@pytest.mark.parametrize(
    ("room_id", "guest_language"),
    [
        (
            uuid.UUID("11111111-1111-1111-1111-111111111111"),
            GuestLanguage.ENGLISH,
        ),
        (
            uuid.UUID("22222222-2222-2222-2222-222222222222"),
            GuestLanguage.Hindi,
        ),
        (
            uuid.UUID("33333333-3333-3333-3333-333333333333"),
            GuestLanguage.HINGLISH,
        ),
    ],
    ids=["english-room", "hindi-room", "hinglish-room"],
)
def test_create_conversation_creates_active_conversation(
    room_id,
    guest_language,
):
    db = MagicMock()
    db.get.return_value = SimpleNamespace(is_active=True)

    with patch("app.services.conversation_services.Conversation") as conversation_model:
        conversation = MagicMock()
        conversation_model.return_value = conversation

        result = ConversationServices.create_conversation(
            db,
            room_id,
            guest_language,
        )

    assert result is conversation
    conversation_model.assert_called_once_with(
        room_id=room_id,
        guest_language=guest_language,
        status=ConversationStatus.ACTIVE,
    )
    db.add.assert_called_once_with(conversation)
    db.commit.assert_called_once_with()
    db.refresh.assert_called_once_with(conversation)


@pytest.mark.parametrize(
    "room",
    [
        None,
        SimpleNamespace(is_active=False),
    ],
    ids=["room-not-found", "inactive-room"],
)
def test_create_conversation_rejects_invalid_or_inactive_room(room):
    db = MagicMock()
    db.get.return_value = room

    with pytest.raises(
        ValueError,
        match="Invalid or inactive hotel room",
    ):
        ConversationServices.create_conversation(
            db,
            uuid.uuid4(),
            GuestLanguage.ENGLISH,
        )

    db.add.assert_not_called()
    db.commit.assert_not_called()
    db.refresh.assert_not_called()


@pytest.mark.parametrize(
    "failing_operation",
    ["commit", "refresh"],
    ids=["commit-failure", "refresh-failure"],
)
def test_create_conversation_rolls_back_when_database_operation_fails(
    failing_operation,
):
    db = MagicMock()
    db.get.return_value = SimpleNamespace(is_active=True)

    database_error = SQLAlchemyError("database failure")
    getattr(db, failing_operation).side_effect = database_error

    with patch("app.services.conversation_services.Conversation") as conversation_model:
        conversation = MagicMock()
        conversation_model.return_value = conversation

        with pytest.raises(SQLAlchemyError, match="database failure"):
            ConversationServices.create_conversation(
                db,
                uuid.uuid4(),
                GuestLanguage.ENGLISH,
            )

    db.add.assert_called_once_with(conversation)
    db.rollback.assert_called_once_with()


@pytest.mark.parametrize(
    "conversation_id",
    [
        uuid.UUID("44444444-4444-4444-4444-444444444444"),
        uuid.UUID("55555555-5555-5555-5555-555555555555"),
    ],
    ids=["primary-conversation", "secondary-conversation"],
)
def test_get_active_conversation_returns_matching_conversation(
    conversation_id,
):
    db = MagicMock()
    expected_conversation = MagicMock()
    db.scalar.return_value = expected_conversation

    result = ConversationServices.get_active_conversation(
        db,
        conversation_id,
    )

    assert result is expected_conversation
    db.scalar.assert_called_once()


def test_get_active_conversation_returns_none_when_not_found():
    db = MagicMock()
    db.scalar.return_value = None

    result = ConversationServices.get_active_conversation(
        db,
        uuid.uuid4(),
    )

    assert result is None
    db.scalar.assert_called_once()


@pytest.mark.parametrize(
    ("role", "content", "expected_content"),
    [
        (
            MessageRole.GUEST,
            " Hello, I need help. ",
            "Hello, I need help.",
        ),
        (
            MessageRole.ASSISTANT,
            "\nYour room is ready.\t",
            "Your room is ready.",
        ),
    ],
    ids=["trimmed-guest-message", "trimmed-assistant-message"],
)
def test_save_message_creates_message_with_trimmed_content(
    role,
    content,
    expected_content,
):
    db = MagicMock()
    db.scalar.return_value = MagicMock()
    conversation_id = uuid.uuid4()

    with patch(
        "app.services.conversation_services.ConversationMessage"
    ) as message_model:
        message = MagicMock()
        message_model.return_value = message

        result = ConversationServices.save_message(
            db,
            conversation_id,
            role,
            content,
        )

    assert result is message
    message_model.assert_called_once_with(
        conversation_id=conversation_id,
        role=role,
        content=expected_content,
    )
    db.add.assert_called_once_with(message)
    db.commit.assert_called_once_with()
    db.refresh.assert_called_once_with(message)


def test_save_message_rejects_missing_or_inactive_conversation():
    db = MagicMock()
    db.scalar.return_value = None

    with pytest.raises(
        ValueError,
        match="Conversation does not exist or has ended",
    ):
        ConversationServices.save_message(
            db,
            uuid.uuid4(),
            MessageRole.GUEST,
            "Hello",
        )

    db.add.assert_not_called()
    db.commit.assert_not_called()
    db.refresh.assert_not_called()


@pytest.mark.parametrize(
    "database_operation",
    ["commit", "refresh"],
    ids=["message-commit-failure", "message-refresh-failure"],
)
def test_save_message_rolls_back_when_database_operation_fails(
    database_operation,
):
    db = MagicMock()
    db.scalar.return_value = MagicMock()

    database_error = SQLAlchemyError("message database failure")
    getattr(db, database_operation).side_effect = database_error

    with patch(
        "app.services.conversation_services.ConversationMessage"
    ) as message_model:
        message = MagicMock()
        message_model.return_value = message

        with pytest.raises(
            SQLAlchemyError,
            match="message database failure",
        ):
            ConversationServices.save_message(
                db,
                uuid.uuid4(),
                MessageRole.GUEST,
                "Hello",
            )

    db.add.assert_called_once_with(message)
    db.rollback.assert_called_once_with()


def test_end_conversation_rolls_back_on_database_error():
    db = MagicMock()
    conversation = SimpleNamespace(
        status=ConversationStatus.ACTIVE,
        ended_at=None,
    )
    db.commit.side_effect = SQLAlchemyError("database failure")

    with patch.object(
        ConversationServices,
        "get_active_conversation",
        return_value=conversation,
    ):
        with pytest.raises(SQLAlchemyError):
            ConversationServices.end_conversation(
                db,
                uuid.uuid4(),
            )

    assert conversation.status == ConversationStatus.ENDED
    db.rollback.assert_called_once()


@pytest.fixture
def conversation_context_data():
    return {
        "conversation_id": uuid.uuid4(),
        "guest_messages": [
            ("Hello", datetime(2026, 1, 1, 10, 0, tzinfo=UTC)),
            ("I need help", datetime(2026, 1, 1, 10, 2, tzinfo=UTC)),
        ],
        "assistant_messages": [
            ("Hello! How can I help?", datetime(2026, 1, 1, 10, 1, tzinfo=UTC)),
            ("Sure, what do you need?", datetime(2026, 1, 1, 10, 3, tzinfo=UTC)),
        ],
    }


def test_get_conversation_context_returns_messages_oldest_first(
    conversation_context_data,
):
    db = MagicMock()

    guest_messages = conversation_context_data["guest_messages"]
    assistant_messages = conversation_context_data["assistant_messages"]

    db.execute.side_effect = [
        MagicMock(all=MagicMock(return_value=guest_messages)),
        MagicMock(all=MagicMock(return_value=assistant_messages)),
    ]

    with patch.object(
        ConversationServices,
        "_validate_conversation",
    ):
        result = ConversationServices.get_conversation_context(
            db,
            conversation_context_data["conversation_id"],
        )

    assert result == [
        {"role": "GUEST", "content": "Hello"},
        {"role": "ASSISTANT", "content": "Hello! How can I help?"},
        {"role": "GUEST", "content": "I need help"},
        {"role": "ASSISTANT", "content": "Sure, what do you need?"},
    ]

    assert db.execute.call_count == 2


def test_get_conversation_context_respects_limit(
    conversation_context_data,
):
    db = MagicMock()

    db.execute.side_effect = [
        MagicMock(
            all=MagicMock(return_value=conversation_context_data["guest_messages"])
        ),
        MagicMock(
            all=MagicMock(return_value=conversation_context_data["assistant_messages"])
        ),
    ]

    with patch.object(
        ConversationServices,
        "_validate_conversation",
    ):
        result = ConversationServices.get_conversation_context(
            db,
            conversation_context_data["conversation_id"],
            limit=2,
        )

    assert len(result) == 2
    assert result == [
        {"role": "GUEST", "content": "I need help"},
        {"role": "ASSISTANT", "content": "Sure, what do you need?"},
    ]


def test_get_conversation_context_returns_empty_list_when_no_messages():
    db = MagicMock()

    db.execute.side_effect = [
        MagicMock(all=MagicMock(return_value=[])),
        MagicMock(all=MagicMock(return_value=[])),
    ]

    with patch.object(
        ConversationServices,
        "_validate_conversation",
    ):
        result = ConversationServices.get_conversation_context(
            db,
            uuid.uuid4(),
        )

    assert result == []


def test_get_conversation_context_validates_conversation():
    db = MagicMock()

    with patch.object(
        ConversationServices,
        "_validate_conversation",
        side_effect=ValueError("Active conversation not found."),
    ) as validate_conversation:
        with pytest.raises(
            ValueError,
            match="Active conversation not found",
        ):
            ConversationServices.get_conversation_context(
                db,
                uuid.uuid4(),
            )

    validate_conversation.assert_called_once()
    db.execute.assert_not_called()


def test_get_pending_proposal_restores_tasks_and_source_input():
    db = MagicMock()
    conversation_id = uuid.uuid4()
    raw_input_id = uuid.uuid4()
    task = ProposedServiceRequest(
        category=RequestCategory.HOUSEKEEPING,
        staff_summary="Deliver two towels",
        priority=RequestPriority.MEDIUM,
    )
    db.scalar.return_value = (
        "I can arrange that.\n[roomly-pending-tasks:"
        f'{{"raw_input_id":"{raw_input_id}",'
        '"tasks":[{"category":"HOUSEKEEPING",'
        '"staff_summary":"Deliver two towels","priority":"MEDIUM"}]}]'
    )

    result = ConversationServices.get_pending_proposal(db, conversation_id)

    assert result == (raw_input_id, [task])
    db.scalar.assert_called_once()


def test_get_conversation_context_includes_structured_pending_tasks():
    db = MagicMock()
    conversation_id = uuid.uuid4()
    assistant_message = (
        "I can arrange that.\n[roomly-pending-tasks:"
        '{"raw_input_id":null,"tasks":[{"category":"HOUSEKEEPING",'
        '"staff_summary":"Deliver two towels","priority":"MEDIUM"}]}]'
    )
    db.execute.side_effect = [
        MagicMock(all=MagicMock(return_value=[])),
        MagicMock(
            all=MagicMock(
                return_value=[
                    (assistant_message, datetime(2026, 1, 1, 10, 0, tzinfo=UTC))
                ]
            )
        ),
    ]

    with patch.object(ConversationServices, "_validate_conversation"):
        result = ConversationServices.get_conversation_context(
            db,
            conversation_id,
        )

    assert len(result) == 1
    assert "Pending service requests" in result[0]["content"]
    assert '"staff_summary":"Deliver two towels"' in result[0]["content"]
