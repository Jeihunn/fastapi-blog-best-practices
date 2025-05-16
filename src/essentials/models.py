from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from starlette_babel import gettext_lazy as _

from src.common.models import Base


class Contact(Base):
    __tablename__ = "contacts"

    phone_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        info={"label": _("Phone number")},
    )
    email: Mapped[str] = mapped_column(
        String(254),
        nullable=False,
        info={"label": _("Email")},
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        info={"label": _("Name")},
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        info={"label": _("Message")},
    )

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"
