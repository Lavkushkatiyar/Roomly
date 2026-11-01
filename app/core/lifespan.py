from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.providers.gnani.client import GnaniClient
from app.providers.gnani.stt import GnaniSTT


@asynccontextmanager
async def lifespan(app: FastAPI):
    gnani_client = GnaniClient(
        api_key_id=settings.GNANI_API_KEY_ID,
    )

    app.state.gnani_client = gnani_client
    app.state.gnani_stt = GnaniSTT(client=gnani_client)

    try:
        yield
    finally:
        await gnani_client.aclose()
