from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from src.common.templates import templates

router = APIRouter()


@router.get("/login", name="login", include_in_schema=False)
def login(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("frontend/login.html", {"request": request})


@router.get("/signup", name="signup", include_in_schema=False)
def signup(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("frontend/signup.html", {"request": request})


@router.get("/forgot-password", name="forgot_password", include_in_schema=False)
def forgot_password(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "frontend/forgot-password.html", {"request": request}
    )


@router.get("/verify-email", name="verify_email", include_in_schema=False)
def verify_email(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "frontend/verify-email.html", {"request": request}
    )


@router.get("/verify", name="verify", include_in_schema=False)
def verify(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("frontend/verify.html", {"request": request})


@router.get("/reset-password", name="reset_password", include_in_schema=False)
def reset_password(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "frontend/reset-password.html", {"request": request}
    )


@router.get("/oauth/callback", name="oauth_callback", include_in_schema=False)
def oauth_callback(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "frontend/oauth-callback.html", {"request": request}
    )
