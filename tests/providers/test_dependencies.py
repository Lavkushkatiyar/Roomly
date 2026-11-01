from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.lifespan import lifespan
from app.providers.gnani.dependencies import get_gnani_stt
from app.providers.gnani.stt import GnaniSTT


@pytest.fixture
def app(monkeypatch):
    from app.core import lifespan as lifespan_module

    client = MagicMock()
    client.aclose = AsyncMock()

    monkeypatch.setattr(
        lifespan_module,
        "GnaniClient",
        lambda **kwargs: client,
    )

    application = FastAPI(lifespan=lifespan)

    return application, client


def test_gnani_stt_initialization_and_cleanup(app):
    application, client = app

    with TestClient(application):
        stt = get_gnani_stt(
            MagicMock(app=application),
        )

        assert isinstance(stt, GnaniSTT)
        assert stt.client is client

    client.aclose.assert_awaited_once()
