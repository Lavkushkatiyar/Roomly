from fastapi import APIRouter

from app.api.raw_input import router as raw_input_router

router = APIRouter()

router.include_router(raw_input_router)
