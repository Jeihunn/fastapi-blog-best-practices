import logging

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from fastapi_limiter.depends import RateLimiter
from fastapi_users import exceptions as fu_exceptions
from sqlalchemy.exc import NoInspectionAvailable
from starlette_babel.translator import gettext

from src.auth.fastapi_users import current_active_user, fastapi_users
from src.auth.manager import UserManager, get_user_manager
from src.common import exceptions as common_exceptions
from src.common.schemas import MessageResponse
from src.common.utils.file_helpers import validate_content_type
from src.core.config import settings
from src.core.storage import get_storage
from src.users.api.v1.schemas import ChangePasswordRequest, UserRead, UserUpdate
from src.users.dependencies import set_request_user, user_identifier
from src.users.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users")

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate, requires_verification=True),  # type: ignore[type-var]
    tags=["users (v1)"],
)


@router.post(
    "/me/profile-image",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    tags=["users (v1)"],
    summary="Upload profile image",
    description="Upload a JPEG/PNG/GIF/WebP image and update the user’s profile.",
    responses={
        status.HTTP_200_OK: {
            "description": "Image uploaded and profile updated",
            "content": {
                "application/json": {
                    "example": {"message": "Profile image updated successfully."}
                }
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized – user not authenticated.",
            "content": {"application/json": {"example": {"detail": "Unauthorized"}}},
        },
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: {
            "description": "Payload too large – file exceeds size limit",
            "content": {
                "application/json": {
                    "example": {"detail": "File too large (6.2 MB > 5 MB)"}
                }
            },
        },
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {
            "description": "Unsupported media type",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unsupported file type: image/tiff. Allowed types: image/jpeg, image/png, image/gif, image/webp"
                    }
                }
            },
        },
    },
)
async def update_my_profile_image(
    file: UploadFile = File(
        ..., description="Image file in JPEG, PNG, GIF or WebP format"
    ),
    current_user: User = Depends(current_active_user),
    user_manager: UserManager = Depends(get_user_manager),
) -> dict[str, str]:
    FIELD_NAME = "profile_image"

    # 1) Retrieve column metadata
    try:
        column = type(current_user).__table__.columns[FIELD_NAME]
    except (KeyError, NoInspectionAvailable):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=gettext("Model field '%(field)s' not found.")
            % {"field": FIELD_NAME},
        )
    meta = column.info or {}
    upload_to = meta.get("upload_to", FIELD_NAME).rstrip("/")
    max_size = meta.get("max_size", 5 * 1024 * 1024)  # default 5 MB
    allowed_types = meta.get("allowed_types")

    # 2) Validate MIME type if configured
    if allowed_types:
        try:
            validate_content_type(file, allowed_types)
        except common_exceptions.UnsupportedMediaTypeError as exc:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=str(exc),
            )

    storage = get_storage()
    old_path = getattr(current_user, FIELD_NAME, None)

    # 3) Upload the new image
    try:
        result = await storage.upload(
            file=file,
            upload_to=upload_to,
            max_size=max_size,
        )
    except common_exceptions.FileSizeLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Unexpected error during file upload: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=gettext("An error occurred while uploading the file."),
        )

    new_db_path = result["db_path"]

    # 4) Update user record with new image path
    try:
        await user_manager.user_db.update(current_user, {FIELD_NAME: new_db_path})
    except Exception:
        logger.error("Database update failed, deleting new file: %s", new_db_path)
        try:
            await storage.delete(new_db_path)
        except Exception as exc:
            logger.warning("Failed to delete new file '%s': %s", new_db_path, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=gettext("Failed to update user profile with new image."),
        )

    # 5) Delete old image if cleanup is enabled
    if settings.FILE_CLEANUP_ENABLED and old_path:
        try:
            await storage.delete(old_path)
        except Exception as exc:
            logger.warning("Failed to delete old file '%s': %s", old_path, exc)

    return {"message": gettext("Profile image updated successfully.")}


@router.delete(
    "/me/profile-image",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["users (v1)"],
    summary="Clear profile image",
    description="Remove the profile image and clear its database field.",
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Profile image cleared."},
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized – user not authenticated.",
            "content": {"application/json": {"example": {"detail": "Unauthorized"}}},
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "No profile image to clear.",
            "content": {
                "application/json": {
                    "example": {"detail": "No profile image to clear."}
                }
            },
        },
    },
)
async def clear_my_profile_image(
    current_user: User = Depends(current_active_user),
    user_manager: UserManager = Depends(get_user_manager),
) -> Response:
    FIELD_NAME = "profile_image"
    old_path = getattr(current_user, FIELD_NAME, None)

    if not old_path:
        # No profile image to clear
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=gettext("No profile image to clear."),
        )

    # 3) Reset the field in the database first
    try:
        await user_manager.user_db.update(current_user, {FIELD_NAME: None})
    except Exception as exc:
        logger.error("Failed to clear profile_image in DB: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=gettext("Failed to clear profile image from user record."),
        )

    # 4) Delete the file if cleanup is enabled
    if settings.FILE_CLEANUP_ENABLED:
        try:
            storage = get_storage()
            await storage.delete(old_path)
        except Exception as exc:
            logger.warning("Failed to remove profile image '%s': %s", old_path, exc)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/me/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    tags=["users (v1)"],
    dependencies=[
        Depends(set_request_user),
        Depends(RateLimiter(times=5, hours=1, identifier=user_identifier)),
    ],
    summary="Change password",
    description="Verify and update the current user's password.",
    responses={
        status.HTTP_200_OK: {
            "description": "Password changed successfully.",
            "content": {
                "application/json": {
                    "example": {"message": "Password changed successfully."}
                }
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Incorrect current password or invalid new password.",
            "content": {
                "application/json": {
                    "example": {"detail": "Current password is incorrect."}
                }
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized – user not authenticated.",
            "content": {"application/json": {"example": {"detail": "Unauthorized"}}},
        },
    },
)
async def change_my_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(current_active_user),
    user_manager: UserManager = Depends(get_user_manager),
) -> dict[str, str]:
    # 1) Verify current password, get updated hash if algorithm changed
    verified, updated_hash = user_manager.password_helper.verify_and_update(
        data.current_password, current_user.hashed_password
    )
    if not verified:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=gettext("Current password is incorrect."),
        )

    # If the hash scheme has improved, persist the new hash
    if updated_hash:
        try:
            await user_manager.user_db.update(
                current_user, {"hashed_password": updated_hash}
            )
        except Exception as exc:
            logger.error("Failed to persist rehashed password: %s", exc)
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=gettext("Failed to update password hash."),
            )

    # 2) Validate and set the new password
    try:
        await user_manager._update(current_user, {"password": data.new_password})
    except fu_exceptions.InvalidPasswordException as exc:
        # Password policy violation
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=exc.reason,
        )
    except Exception as exc:
        logger.error("Unexpected error during password update: %s", exc)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=gettext("An error occurred while changing the password."),
        )

    return {"message": gettext("Password changed successfully.")}
