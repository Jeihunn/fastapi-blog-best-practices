from typing import cast

from sqladmin import Admin, ModelView
from starlette_babel import gettext_lazy as _
from wtforms import EmailField

from src.essentials.models import Contact


class ContactAdmin(ModelView, model=Contact):
    name = _("Contact")
    name_plural = _("Contacts")
    icon = "fa fa-address-book"
    category = _("General")

    column_labels = {
        "id": cast(str, Contact.id.info.get("label")),
        "phone_number": cast(str, Contact.phone_number.info.get("label")),
        "email": cast(str, Contact.email.info.get("label")),
        "name": cast(str, Contact.name.info.get("label")),
        "message": cast(str, Contact.message.info.get("label")),
        "created_at": cast(str, Contact.created_at.info.get("label")),
        "updated_at": cast(str, Contact.updated_at.info.get("label")),
    }

    column_list = [
        "id",
        "phone_number",
        "email",
        "name",
        "created_at",
        "updated_at",
    ]
    column_searchable_list = ["id", "phone_number", "email", "name"]
    column_sortable_list = column_list
    column_default_sort = ("created_at", True)
    column_details_list = [
        "id",
        "phone_number",
        "email",
        "name",
        "message",
        "created_at",
        "updated_at",
    ]
    form_columns = [
        "phone_number",
        "email",
        "name",
        "message",
    ]
    form_overrides = {
        "email": EmailField,
    }


def register_essentials_admin_views(admin: Admin) -> None:
    admin.add_view(ContactAdmin)
