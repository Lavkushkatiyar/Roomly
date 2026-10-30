from unittest.mock import MagicMock, patch

import pytest

from app.db.session import get_db


def test_get_db_yields_session_and_closes_it() -> None:
    mock_session = MagicMock()

    with patch(
        "app.db.session.SessionLocal",
        return_value=mock_session,
    ):
        generator = get_db()

        session = next(generator)

        assert session is mock_session

        try:
            next(generator)
        except StopIteration:
            pass

        mock_session.close.assert_called_once()


def test_get_db_closes_session_when_request_fails() -> None:
    mock_session = MagicMock()
    error = RuntimeError("Request failed")

    with patch(
        "app.db.session.SessionLocal",
        return_value=mock_session,
    ):
        generator = get_db()

        assert next(generator) is mock_session

        with pytest.raises(RuntimeError, match="Request failed"):
            generator.throw(error)

        mock_session.close.assert_called_once()
