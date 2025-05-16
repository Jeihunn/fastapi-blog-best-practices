from typing import Any, Dict, List, cast

import sqlalchemy.exc
from fastapi_users.password import PasswordHelper
from markupsafe import Markup
from sqladmin import Admin, BaseView, ModelView, expose
from sqladmin.fields import FileField
from starlette import status
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette_babel import gettext_lazy as _
from wtforms import EmailField, PasswordField

from src.common.admin.file_upload import FileUploadMixin
from src.common.utils.file_helpers import get_public_url
from src.users.models import OAuthAccount, User

password_helper = PasswordHelper()


class PasswordResetView(BaseView):
    """
    Provides an admin-only endpoint for resetting a user's password.
    Exposed at /users/{pk}/reset-password for GET and POST requests.
    """

    name = _("Reset password")
    identity = "reset_password"
    icon = "fa-solid fa-lock"

    def is_visible(self, request: Request) -> bool:
        """
        Hide this view from the main admin menu; only accessible via detail page.
        """
        return False

    @expose(
        "/user/reset-password/{pk}",
        methods=["GET", "POST"],
        identity="reset_password",
        include_in_schema=False,
    )
    async def reset_password(self, request: Request) -> Response:
        """
        GET:  Show the password-reset form.
        POST: Validate & hash the new password, update user, then redirect.
        """
        template = "admin/users/UserAdmin/reset_password.html"
        pk: str = request.path_params["pk"]

        # Load user from DB
        async with self._admin_ref.session_maker() as session:
            try:
                user = await session.get(User, pk)
            except sqlalchemy.exc.DBAPIError:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Helper to render form (with optional error & status code)
        async def render_form(
            error: str | None = None, code: int = status.HTTP_200_OK
        ) -> Response:
            ctx = {"request": request, "user": user}
            if error:
                ctx["error"] = error
            return await self.templates.TemplateResponse(
                request, template, ctx, status_code=code
            )

        # GET → render empty form
        if request.method == "GET":
            return await render_form()

        # POST → read & validate
        form = await request.form()
        raw_new_pw = form.get("new_password")
        raw_confirm = form.get("confirm_password")

        # Ensure both fields are non-empty strings
        if (
            not raw_new_pw
            or not raw_confirm
            or not isinstance(raw_new_pw, str)
            or not isinstance(raw_confirm, str)
        ):
            return await render_form(
                error=_("Both password fields must be non-empty strings."),
                code=status.HTTP_400_BAD_REQUEST,
            )

        new_pw: str = raw_new_pw
        confirm: str = raw_confirm

        # Check they match
        if new_pw != confirm:
            return await render_form(
                error=_("The passwords do not match."),
                code=status.HTTP_400_BAD_REQUEST,
            )

        # Update password
        async with self._admin_ref.session_maker() as session:
            user.hashed_password = password_helper.hash(new_pw)
            session.add(user)
            await session.commit()

        # Redirect to details
        return RedirectResponse(
            request.url_for("admin:details", identity="user", pk=pk),
            status_code=status.HTTP_303_SEE_OTHER,
        )


class UserAdmin(FileUploadMixin, model=User):
    name = _("User")
    name_plural = _("Users")
    icon = "fa-solid fa-user"
    category = _("Account")
    details_template = "admin/users/UserAdmin/details.html"

    @staticmethod
    def _fmt_profile_image(model: Any, col: Any) -> Markup:
        if not model.profile_image:
            return Markup("")
        url = get_public_url(model.profile_image)
        return Markup(
            f'<img src="{url}" '
            'style="height:50px;object-fit:cover;border-radius:4px;" />'
        )

    @staticmethod
    def _fmt_oauth_accounts(model: Any, col: Any) -> List[str]:
        return [f"{acc.oauth_name} ({acc.account_id})" for acc in model.oauth_accounts]

    column_labels = {
        "id": _("ID"),
        "email": _("Email"),
        "hashed_password": _("Password"),
        "is_active": _("Active"),
        "is_superuser": _("Superuser"),
        "is_verified": _("Verified"),
        "first_name": cast(str, User.first_name.info.get("label")),
        "last_name": cast(str, User.last_name.info.get("label")),
        "profile_image": cast(str, User.profile_image.info.get("label")),
        "date_joined": cast(str, User.date_joined.info.get("label")),
        "last_login": cast(str, User.last_login.info.get("label")),
        "updated_at": cast(str, User.updated_at.info.get("label")),
        "oauth_accounts": cast(str, User.oauth_accounts.info.get("label")),
    }

    column_list = [
        "id",
        "email",
        "profile_image",
        "first_name",
        "last_name",
        "is_active",
        "is_superuser",
        "is_verified",
        "date_joined",
        "last_login",
        "updated_at",
    ]
    column_formatters = {"profile_image": _fmt_profile_image}
    column_searchable_list = ["id", "email", "first_name", "last_name"]
    column_sortable_list = column_list
    column_default_sort = ("date_joined", True)
    column_details_list = [
        "id",
        "email",
        "hashed_password",
        "first_name",
        "last_name",
        "profile_image",
        "is_active",
        "is_superuser",
        "is_verified",
        "date_joined",
        "last_login",
        "updated_at",
        "oauth_accounts",
    ]
    column_formatters_detail = {"oauth_accounts": _fmt_oauth_accounts}
    form_columns = [
        "email",
        "hashed_password",
        "first_name",
        "last_name",
        "profile_image",
        "is_active",
        "is_superuser",
        "is_verified",
    ]
    form_overrides = {
        "email": EmailField,
        "hashed_password": PasswordField,
        "profile_image": FileField,
    }
    form_create_rules = ["email", "hashed_password"]
    form_edit_rules = [
        "email",
        "first_name",
        "last_name",
        "profile_image",
        "is_active",
        "is_superuser",
        "is_verified",
    ]

    async def on_model_change(
        self,
        data: Dict[str, Any],
        model: Any,
        is_created: bool,
        request: Request,
    ) -> None:
        await super().on_model_change(data, model, is_created, request)

        raw_pw_any = data.pop("hashed_password", None)
        if raw_pw_any is not None:
            if not isinstance(raw_pw_any, str):
                raise ValueError("Password must be a string")
            data["hashed_password"] = password_helper.hash(raw_pw_any)


class OAuthAccountAdmin(ModelView, model=OAuthAccount):
    name = _("OAuth account")
    name_plural = _("OAuth accounts")
    icon = "fa-solid fa-user-shield"
    category = _("Account")
    can_create = False
    can_edit = False

    column_labels = {
        "id": _("ID"),
        "user_id": _("User ID"),
        "oauth_name": _("OAuth name"),
        "access_token": _("Access token"),
        "expires_at": _("Expires at"),
        "refresh_token": _("Refresh token"),
        "account_id": _("Account ID"),
        "account_email": _("Account email"),
        "created_at": cast(str, OAuthAccount.created_at.info.get("label")),
        "updated_at": cast(str, OAuthAccount.updated_at.info.get("label")),
    }

    column_list = [
        "id",
        "user_id",
        "oauth_name",
        "account_id",
        "account_email",
        "created_at",
        "updated_at",
    ]
    column_searchable_list = column_list
    column_sortable_list = column_list
    column_default_sort = ("created_at", True)
    column_details_list = [
        "id",
        "user_id",
        "oauth_name",
        "access_token",
        "expires_at",
        "refresh_token",
        "account_id",
        "account_email",
        "created_at",
        "updated_at",
    ]


def register_users_admin_views(admin: Admin) -> None:
    admin.add_view(UserAdmin)
    admin.add_view(OAuthAccountAdmin)
    admin.add_view(PasswordResetView)
