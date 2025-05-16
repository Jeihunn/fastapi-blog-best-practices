from fastapi import APIRouter

from src.auth.fastapi_users import auth_backend, fastapi_users
from src.auth.oauth2 import google_oauth_client
from src.core.config import settings
from src.users.api.v1.schemas import UserCreate, UserRead

router = APIRouter()

router.include_router(
    fastapi_users.get_auth_router(auth_backend, requires_verification=True),
    prefix="/auth/jwt",
    tags=["auth (v1)"],
)
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth (v1)"],
)
router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth (v1)"],
)
router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth (v1)"],
)
router.include_router(
    fastapi_users.get_oauth_router(
        google_oauth_client,
        auth_backend,
        settings.SECRET_KEY,
        redirect_url=f"{str(settings.FRONTEND_URL).rstrip('/')}/oauth/callback",
        associate_by_email=True,
        is_verified_by_default=True,
    ),
    prefix="/auth/google",
    tags=["oauth (v1)"],
)
# router.include_router(
#     fastapi_users.get_oauth_associate_router(
#         google_oauth_client,
#         UserRead,
#         settings.SECRET_KEY,
#         redirect_url=f"{str(settings.FRONTEND_URL).rstrip('/')}/oauth/google",
#         requires_verification=True,
#     ),
#     prefix="/auth/google/associate",
#     tags=["oauth (v1)"],
# )
