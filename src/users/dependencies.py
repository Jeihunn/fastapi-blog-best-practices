from fastapi import Depends, Request

from src.auth.fastapi_users import current_active_user
from src.users.models import User


async def set_request_user(
    request: Request,
    current_user: User = Depends(current_active_user),
) -> User:
    """
    Dependency that retrieves the current active user and stores it
    in request.state.user for downstream use (e.g., rate limiting).
    """
    request.state.user = current_user
    return current_user


async def user_identifier(request: Request) -> str:
    """
    RateLimiter identifier function that returns the user ID
    stored in request.state.user. Used for user-based rate limiting.
    """
    # At this point, set_request_user must have run to populate request.state.user
    return f"{request.state.user.id}:{request.scope['path']}"
