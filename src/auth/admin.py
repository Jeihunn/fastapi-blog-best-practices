import logging
import uuid
from typing import Union

from fastapi_users.password import PasswordHelper
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqladmin.authentication import (
    AuthenticationBackend as SQLAdminAuthenticationBackend,
)
from starlette.requests import Request
from starlette.responses import Response

from src.core.config import settings
from src.core.database import async_session_maker
from src.users.models import OAuthAccount, User

logger = logging.getLogger(__name__)

password_helper = PasswordHelper()


class AdminAuth(SQLAdminAuthenticationBackend):
    def __init__(self, secret_key: str) -> None:
        super().__init__(secret_key)

    async def login(self, request: Request) -> bool:
        form = await request.form()
        raw_username = form.get("username")
        raw_password = form.get("password")
        if not raw_username or not raw_password:
            logger.debug("Login attempt with missing credentials")
            return False

        if not isinstance(raw_username, str):
            logger.debug("Invalid username type")
            return False
        if not isinstance(raw_password, str):
            logger.debug("Invalid password type")
            return False

        email = raw_username
        password = raw_password

        async with async_session_maker() as session:
            user_db: SQLAlchemyUserDatabase[User, uuid.UUID] = SQLAlchemyUserDatabase(
                session, User, OAuthAccount
            )
            user = await user_db.get_by_email(email)
            if user is None:
                logger.warning(f"Login failed: user not found ({email})")
                return False

            valid, new_hash = password_helper.verify_and_update(
                password, user.hashed_password
            )
            if not valid:
                logger.warning(f"Login failed: invalid password for {email}")
                return False

            if new_hash:
                await user_db.update(user, {"hashed_password": new_hash})

            if not user.is_superuser:
                logger.warning(f"Login failed: not a superuser ({email})")
                return False

            request.session["user_id"] = str(user.id)
            logger.info(f"User logged in successfully: {email}")

        return True

    async def logout(self, request: Request) -> bool:
        user_id = request.session.get("user_id")
        request.session.clear()
        logger.info(f"User logged out: {user_id}")
        return True

    async def authenticate(self, request: Request) -> Union[bool, Response]:
        user_id = request.session.get("user_id")
        if not user_id:
            return False

        async with async_session_maker() as session:
            user_db: SQLAlchemyUserDatabase[User, uuid.UUID] = SQLAlchemyUserDatabase(
                session, User, OAuthAccount
            )
            user = await user_db.get(user_id)
            if not user or not user.is_superuser:
                logger.warning(f"Authenticate failed for user_id: {user_id}")
                return False

            request.state.user = user

        return True


admin_auth = AdminAuth(settings.SECRET_KEY)
