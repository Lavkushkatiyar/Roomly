import logging

from fastapi import FastAPI

from app.api.hotel_room import router as hotel_room_router
from app.api.raw_input import router as raw_input_router
from app.api.service_request import router as service_request_router
from app.api.task_extraction import router as task_extraction_router
from app.core.config import settings
from app.core.lifespan import lifespan
from app.core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


app = FastAPI(lifespan=lifespan, title=settings.app_name, version=settings.app_version)
app.include_router(hotel_room_router)
app.include_router(raw_input_router)
app.include_router(service_request_router)
app.include_router(task_extraction_router)


@app.get("/")
async def home_page() -> dict[str, str]:
    logger.info("Home page accessed ")
    return {"status": "Awesome", "message": "Ready for roomly ? "}


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    logger.info("Health check requested")
    return {"status": "ok"}


@app.get("/ready", tags=["Health"])
async def ready_check() -> dict[str, str]:
    logger.info("Ready check requested")
    return {"status": "ready"}
