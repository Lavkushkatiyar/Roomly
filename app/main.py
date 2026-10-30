import logging

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


app = FastAPI(title=settings.app_name, version=settings.app_version)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    logger.info("Health check requested")
    return {"status": "ok"}


@app.get("/ready", tags=["Health"])
async def ready_check() -> dict[str, str]:
    logger.info("Ready check requested")
    return {"status": "ready"}
