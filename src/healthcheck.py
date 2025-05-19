from fastapi import APIRouter, status
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


router = APIRouter(
    prefix="/api",
    tags=["Health"],
)


@router.get(
    "/healthcheck",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
)
async def health_check() -> dict[str, str]:
    return {"status": "OK"}
