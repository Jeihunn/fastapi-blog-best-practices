from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from src.common.templates import templates

router = APIRouter()


@router.get("/account/profile", name="profile", include_in_schema=False)
def profile(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("frontend/profile.html", {"request": request})
