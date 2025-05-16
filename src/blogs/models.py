import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from fastapi_users_db_sqlalchemy.generics import GUID
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import ColumnElement
from starlette_babel import gettext_lazy as _

from src.common.models import AutoSlugMixin, Base
from src.core.config import settings

if TYPE_CHECKING:
    from src.users.models import User

# --- Association Tables ---
blogpost_categories = Table(
    "blogpost_categories",
    Base.metadata,
    Column(
        "blogpost_id",
        GUID,
        ForeignKey("blog_posts.id", ondelete="CASCADE"),
        primary_key=True,
        info={"label": _("BlogPost")},
    ),
    Column(
        "category_id",
        GUID,
        ForeignKey("categories.id", ondelete="CASCADE"),
        primary_key=True,
        info={"label": _("Category")},
    ),
    comment="Association table for BlogPosts and Categories",
)

blogpost_tags = Table(
    "blogpost_tags",
    Base.metadata,
    Column(
        "blogpost_id",
        GUID,
        ForeignKey("blog_posts.id", ondelete="CASCADE"),
        primary_key=True,
        info={"label": _("BlogPost")},
    ),
    Column(
        "tag_id",
        GUID,
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
        info={"label": _("Tag")},
    ),
    comment="Association table for BlogPosts and Tags",
)


# --- Models ---
class Category(Base, AutoSlugMixin):
    __tablename__ = "categories"
    __slug_source__ = "name"

    # --- Normal Fields ---
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        info={"label": _("Name")},
    )
    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        info={"label": _("Slug")},
    )

    # --- Relationships ---
    blogposts: Mapped[List["BlogPost"]] = relationship(
        "BlogPost",
        secondary=blogpost_categories,
        back_populates="categories",
        lazy="selectin",
        info={"label": _("Blog posts")},
    )

    def __str__(self) -> str:
        return self.name


class Tag(Base, AutoSlugMixin):
    __tablename__ = "tags"
    __slug_source__ = "name"

    # --- Normal Fields ---
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        info={"label": _("Name")},
    )
    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        info={"label": _("Slug")},
    )

    # --- Relationships ---
    blogposts: Mapped[List["BlogPost"]] = relationship(
        "BlogPost",
        secondary=blogpost_tags,
        back_populates="tags",
        lazy="selectin",
        info={"label": _("Blog posts")},
    )

    def __str__(self) -> str:
        return self.name


class BlogPost(Base, AutoSlugMixin):
    __tablename__ = "blog_posts"
    __slug_source__ = "title"

    # --- Foreign Key Fields ---
    author_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        info={"label": _("Author ID")},
    )

    # --- Normal Fields ---
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        info={"label": _("Title")},
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        info={"label": _("Content")},
    )
    cover_image: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=False,
        info={
            "label": _("Cover image"),
            "file": True,
            "upload_to": "blog_covers/",
            "max_size": 5 * 1024 * 1024,
            "allowed_types": settings.IMAGE_UPLOAD_ALLOWED_TYPES,
        },
    )
    is_published: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        index=True,
        server_default="false",
        info={"label": _("Published")},
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        info={"label": _("Published at")},
    )
    slug: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        unique=True,
        index=True,
        info={"label": _("Slug")},
    )

    # --- Relationships ---
    author: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="blogposts",
        lazy="joined",
        info={"label": _("Author")},
    )
    categories: Mapped[List["Category"]] = relationship(
        "Category",
        secondary=blogpost_categories,
        back_populates="blogposts",
        lazy="selectin",
        info={"label": _("Categories")},
    )
    tags: Mapped[List["Tag"]] = relationship(
        "Tag",
        secondary=blogpost_tags,
        back_populates="blogposts",
        lazy="selectin",
        info={"label": _("Tags")},
    )
    comments: Mapped[List["Comment"]] = relationship(
        "Comment",
        back_populates="blogpost",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select",
        info={"label": _("Comments")},
    )
    likes: Mapped[List["BlogLike"]] = relationship(
        "BlogLike",
        back_populates="blogpost",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select",
        info={"label": _("Likes")},
    )

    @hybrid_property
    def likes_count(self) -> int:
        return len(self.likes or [])

    @likes_count.expression
    def _likes_count_expr(cls) -> ColumnElement[int]:
        return (
            select(func.count(BlogLike.user_id))
            .where(BlogLike.blogpost_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def comments_count(self) -> int:
        return len(self.comments or [])

    @comments_count.expression
    def _comments_count_expr(cls) -> ColumnElement[int]:
        return (
            select(func.count(Comment.id))
            .where(Comment.blogpost_id == cls.id)
            .scalar_subquery()
        )

    def __str__(self) -> str:
        return self.title


class Comment(Base):
    __tablename__ = "comments"

    # --- Foreign Key Fields ---
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        info={"label": _("User ID")},
    )
    blogpost_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("blog_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        info={"label": _("Blog post ID")},
    )

    # --- Normal Fields ---
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        info={"label": _("Content")},
    )

    # --- Relationships ---
    user: Mapped["User"] = relationship(
        "User",
        back_populates="comments",
        lazy="joined",
        info={"label": _("User")},
    )
    blogpost: Mapped["BlogPost"] = relationship(
        "BlogPost",
        back_populates="comments",
        info={"label": _("Blog post")},
    )

    def __str__(self) -> str:
        return f"Comment by {self.user} on {self.blogpost} - {self.content[:30]}..."


class BlogLike(Base):
    __tablename__ = "blog_likes"
    __table_args__ = (
        UniqueConstraint("user_id", "blogpost_id", name="uq_user_blogpost_like"),
        {"comment": "Ensures a user can like a blog post only once"},
    )

    # --- Foreign Key Fields ---
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        info={"label": _("User ID")},
    )
    blogpost_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("blog_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        info={"label": _("Blog post ID")},
    )

    # --- Relationships ---
    user: Mapped["User"] = relationship(
        "User",
        back_populates="blog_likes",
        lazy="joined",
        info={"label": _("User")},
    )
    blogpost: Mapped["BlogPost"] = relationship(
        "BlogPost",
        back_populates="likes",
        info={"label": _("Blog post")},
    )

    def __str__(self) -> str:
        return f"Like by {self.user} on {self.blogpost}"
