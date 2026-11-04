import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.db.models.enums import (
    ConversationStatus,
    GuestLanguage,
    MessageRole,
)
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


@pytest.mark.parametrize(
    ("database_messages", "expected_messages", "limit"),
    [
        (
            ["newest", "middle", "oldest"],
            ["oldest", "middle", "newest"],
            10,
        ),
        (
            ["third", "second"],
            ["second", "third"],
            2,
        ),
        (
            [],
            [],
            10,
        ),
    ],
    ids=[
        "default-limit-orders-messages",
        "custom-limit-orders-messages",
        "empty-context",
    ],
)
def test_get_conversation_context_returns_messages_oldest_first(
    database_messages,
    expected_messages,
    limit,
):
    db = MagicMock()
    db.scalars.return_value.all.return_value = database_messages

    result = ConversationServices.get_conversation_context(
        db,
        uuid.uuid4(),
        limit=limit,
    )

    assert result == expected_messages
    db.scalars.assert_called_once()


def test_end_conversation_marks_conversation_as_ended():
    db = MagicMock()
    conversation = SimpleNamespace(
        status=ConversationStatus.ACTIVE,
        ended_at=None,
    )

    with patch.object(
        ConversationServices,
        "get_active_conversation",
        return_value=conversation,
    ):
        result = ConversationServices.end_conversation(
            db,
            uuid.uuid4(),
        )

    assert result is conversation
    assert conversation.status == ConversationStatus.ENDED
    assert conversation.ended_at is not None
    assert conversation.ended_at.tzinfo is not None

    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(conversation)


def test_end_conversation_returns_none_when_not_active():
    db = MagicMock()

    with patch.object(
        ConversationServices,
        "get_active_conversation",
        return_value=None,
    ):
        result = ConversationServices.end_conversation(
            db,
            uuid.uuid4(),
        )

    assert result is None
    db.commit.assert_not_called()
    db.refresh.assert_not_called()


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
