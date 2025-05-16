from fastapi import APIRouter

from src.blogs.api.v1.router import router as v1_router

router = APIRouter()

router.include_router(
    v1_router,
    prefix="/api/v1",
)
