from datetime import datetime
from typing import List, Optional

from fastapi_users_db_sqlalchemy import (
    SQLAlchemyBaseOAuthAccountTableUUID,
    SQLAlchemyBaseUserTableUUID,
)
from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from starlette_babel import gettext_lazy as _

from src.blogs.models import BlogLike, BlogPost, Comment
from src.common.models import BaseModel, TimeStampMixin
from src.core.config import settings


class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, TimeStampMixin, BaseModel):
    pass


class User(SQLAlchemyBaseUserTableUUID, BaseModel):
    # --- Normal Fields ---
    date_joined: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        info={"label": _("Date joined")},
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        info={"label": _("Last login")},
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        info={"label": _("Updated at")},
    )
    first_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        info={"label": _("First name")},
    )
    last_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        info={"label": _("Last name")},
    )
    profile_image: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        info={
            "label": _("Profile image"),
            "file": True,
            "upload_to": "profile_images/",
            "max_size": 5 * 1024 * 1024,
            "allowed_types": settings.IMAGE_UPLOAD_ALLOWED_TYPES,
        },
    )

    # --- Relationships ---
    oauth_accounts: Mapped[List["OAuthAccount"]] = relationship(
        "OAuthAccount",
        lazy="joined",
        cascade="all, delete-orphan",
        passive_deletes=True,
        info={"label": _("OAuth accounts")},
    )
    blogposts: Mapped[List["BlogPost"]] = relationship(
        "BlogPost",
        back_populates="author",
        lazy="select",
        info={"label": _("Blog posts")},
    )
    comments: Mapped[List["Comment"]] = relationship(
        "Comment",
        back_populates="user",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
        info={"label": _("Comments")},
    )
    blog_likes: Mapped[List["BlogLike"]] = relationship(
        "BlogLike",
        back_populates="user",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
        info={"label": _("Blog Likes")},
    )

    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or self.email

    def __str__(self) -> str:
        if self.first_name or self.last_name:
            return f"{self.full_name} <{self.email}>"
        return self.email
