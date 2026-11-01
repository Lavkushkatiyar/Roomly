from fastapi import APIRouter

from app.api.hotel_room import router as hotel_room_router
from app.api.raw_input import router as raw_input_router
from app.api.service_request import router as service_request_router
from app.api.task_extraction import router as task_extraction_router
from app.api.voice_ingestion import router as voice_router

api_router = APIRouter()

api_router.include_router(hotel_room_router)
api_router.include_router(raw_input_router)
api_router.include_router(service_request_router)
api_router.include_router(task_extraction_router)
api_router.include_router(voice_router)
