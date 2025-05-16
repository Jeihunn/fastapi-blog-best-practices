from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from src.common.templates import templates

router = APIRouter()


@router.get("/", name="home", include_in_schema=False)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("frontend/index.html", {"request": request})


@router.get("/about", name="about", include_in_schema=False)
def about(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("frontend/about.html", {"request": request})


@router.get("/contact", name="contact", include_in_schema=False)
def contact(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("frontend/contact.html", {"request": request})
