import re
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import httpx
from fastapi import Depends, Request, Response
from fastapi_mail import MessageType
from fastapi_users import (
    BaseUserManager,
    UUIDIDMixin,
    exceptions,
    models,
    schemas,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from starlette.datastructures import UploadFile
from starlette_babel.translator import gettext

from src.auth.dependencies import get_user_db
from src.common.mail.sender import send_email
from src.core import path_conf
from src.core.config import settings
from src.users.models import User


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def on_after_login(
        self,
        user: User,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
    ) -> None:
        now = datetime.now(timezone.utc)
        await self.user_db.update(user, {"last_login": now})

    async def on_after_register(
        self, user: User, request: Optional[Request] = None
    ) -> None:
        if not user.is_verified:
            await self.request_verify(user, request)

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ) -> None:
        verify_link = f"{str(settings.FRONTEND_URL).rstrip('/')}/verify?token={token}"
        context = {
            "request": request,
            "user": user,
            "verify_link": verify_link,
        }
        attachments: List[Union[UploadFile, Dict[str, Any], str]] = [
            {
                "file": str(path_conf.STATIC_DIR / "assets" / "img" / "logo.png"),
                "headers": {
                    "Content-Disposition": "inline; filename=logo.png",
                    "Content-Type": "image/png",
                    "Content-ID": "<company_logo>",
                },
            },
        ]
        await send_email(
            subtype=MessageType.html,
            attachments=attachments,
            recipients=[user.email],
            subject=gettext("Email Verification Request"),
            template_name="emails/verify_email.html",
            template_body=context,
        )

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ) -> None:
        reset_link = (
            f"{str(settings.FRONTEND_URL).rstrip('/')}/reset-password?token={token}"
        )
        context = {
            "request": request,
            "user": user,
            "reset_link": reset_link,
        }
        attachments: List[Union[UploadFile, Dict[str, Any], str]] = [
            {
                "file": str(path_conf.STATIC_DIR / "assets" / "img" / "logo.png"),
                "headers": {
                    "Content-Disposition": "inline; filename=logo.png",
                    "Content-Type": "image/png",
                    "Content-ID": "<company_logo>",
                },
            },
        ]
        await send_email(
            subtype=MessageType.html,
            recipients=[user.email],
            attachments=attachments,
            subject=gettext("Password Reset Request"),
            template_name="emails/reset_password.html",
            template_body=context,
        )

    async def validate_password(
        self, password: str, user: Union[schemas.UC, models.UP]
    ) -> None:
        """
        Validate the password against common security rules.
        Raises InvalidPasswordException with a localized message on failure.
        """

        # 1. Minimum length check
        min_length = settings.PASSWORD_MIN_LENGTH
        if len(password) < min_length:
            message = gettext(
                "Password must be at least %(min_length)d characters long."
            ) % {"min_length": min_length}
            raise exceptions.InvalidPasswordException(reason=message)

        # 2. Cannot contain the email username part
        if user.email:
            email_local_part = user.email.split("@")[0].lower()
            if email_local_part in password.lower():
                raise exceptions.InvalidPasswordException(
                    reason=gettext(
                        "Password cannot contain parts of your email address."
                    )
                )

        # 3. Must contain at least one uppercase letter
        if not re.search(r"[A-Z]", password):
            raise exceptions.InvalidPasswordException(
                reason=gettext("Password must include at least one uppercase letter.")
            )

        # 4. Must contain at least one lowercase letter
        if not re.search(r"[a-z]", password):
            raise exceptions.InvalidPasswordException(
                reason=gettext("Password must include at least one lowercase letter.")
            )

        # 5. Must contain at least one digit
        if not re.search(r"\d", password):
            raise exceptions.InvalidPasswordException(
                reason=gettext("Password must include at least one digit.")
            )

        # 6. Must contain at least one special character
        if not re.search(r"[^\w\s]", password):
            raise exceptions.InvalidPasswordException(
                reason=gettext(
                    "Password must include at least one special character (e.g. !@#%)."
                )
            )

        return

    async def oauth_callback(
        self: "BaseUserManager[models.UOAP, models.ID]",
        oauth_name: str,
        access_token: str,
        account_id: str,
        account_email: str,
        expires_at: Optional[int] = None,
        refresh_token: Optional[str] = None,
        request: Optional[Request] = None,
        *,
        associate_by_email: bool = False,
        is_verified_by_default: bool = False,
    ) -> models.UOAP:
        oauth_account_dict = {
            "oauth_name": oauth_name,
            "access_token": access_token,
            "account_id": account_id,
            "account_email": account_email,
            "expires_at": expires_at,
            "refresh_token": refresh_token,
        }

        try:
            user = await self.get_by_oauth_account(oauth_name, account_id)
        except exceptions.UserNotExists:
            try:
                # Associate account
                user = await self.get_by_email(account_email)
                if not associate_by_email:
                    raise exceptions.UserAlreadyExists()
                user = await self.user_db.add_oauth_account(user, oauth_account_dict)
            except exceptions.UserNotExists:
                # Create account
                password = self.password_helper.generate()
                profile_fields: Dict[str, Optional[str]] = (
                    await self._fetch_oauth_provider_fields(oauth_name, access_token)  # type: ignore[attr-defined]
                )

                user_dict = {
                    "email": account_email,
                    "first_name": profile_fields.get("first_name"),
                    "last_name": profile_fields.get("last_name"),
                    "profile_image": profile_fields.get("profile_image"),
                    "hashed_password": self.password_helper.hash(password),
                    "is_verified": is_verified_by_default,
                }
                user = await self.user_db.create(user_dict)
                user = await self.user_db.add_oauth_account(user, oauth_account_dict)
                await self.on_after_register(user, request)
        else:
            # Update oauth
            for existing_oauth_account in user.oauth_accounts:
                if (
                    existing_oauth_account.account_id == account_id
                    and existing_oauth_account.oauth_name == oauth_name
                ):
                    user = await self.user_db.update_oauth_account(
                        user, existing_oauth_account, oauth_account_dict
                    )

        return user

    async def _fetch_oauth_provider_fields(
        self, oauth_name: str, access_token: str
    ) -> Dict[str, Optional[str]]:
        oauth_name_lower = oauth_name.lower()
        if oauth_name_lower == "google":
            return await self._fetch_google_profile(access_token)
        return {}

    async def _fetch_google_profile(
        self, access_token: str
    ) -> Dict[str, Optional[str]]:
        url = "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {"alt": "json"}
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        return {
            "first_name": data.get("given_name"),
            "last_name": data.get("family_name"),
            "profile_image": data.get("picture"),
        }


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase[User, uuid.UUID] = Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    yield UserManager(user_db)
