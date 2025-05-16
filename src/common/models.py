import uuid
from datetime import datetime
from typing import Any, Callable, Union
from uuid import uuid4

from fastapi_users_db_sqlalchemy.generics import GUID
from slugify import slugify
from sqlalchemy import DateTime, event, func
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Mapper,
    declared_attr,
    mapped_column,
    object_session,
)
from starlette_babel import gettext_lazy as _


class AutoSlugMixin:
    """
    This mixin automatically generates a slug before insert or update
    by taking the value from the __slug_source__ field or callable
    and writing its slugified form into the slug column. If the generated slug
    already exists in the database, it appends -1, -2, ... to make it unique.
    If slugify returns an empty string, it assigns a uuid4 instead.

    Usage examples:
        # Simple field-based source
        __slug_source__ = 'name'

        # Callable source, combining multiple fields
        __slug_source__ = lambda self: f"{self.name}-{self.category.title()}"

        # Method-based source
        def custom_slug_source(self):
            return f"{self.name}-{self.id}"
        __slug_source__ = 'custom_slug_source'
    """

    __slug_source__: Union[str, Callable[..., Any]]
    __slug_target__: str = "slug"

    @classmethod
    def __declare_last__(cls) -> None:
        def generate_slug(
            mapper: Mapper[Any],
            connection: Connection,
            target: Any,
        ) -> None:
            # Determine the raw source
            source_src = cls.__slug_source__
            raw = None
            if callable(source_src):
                try:
                    raw = source_src(target)
                except Exception:
                    raw = None
            else:
                attr = getattr(target, source_src, None)
                if callable(attr):
                    try:
                        raw = attr()
                    except Exception:
                        raw = None
                else:
                    raw = attr

            # Do nothing if source is empty or not a string
            if not raw or not isinstance(raw, (str, bytes)):
                return

            source_val = raw.decode("utf-8") if isinstance(raw, bytes) else raw
            # Generate base slug
            base_slug = slugify(source_val)
            session = object_session(target)

            # If slugify yields an empty string, assign a uuid4
            if not base_slug:
                slug = str(uuid4())
            else:
                slug = base_slug
                if session is not None:
                    Model = type(target)
                    current_id = getattr(target, "id", None)
                    # Fetch all matching slugs in one query
                    pattern = f"{base_slug}%"
                    query = session.query(getattr(Model, cls.__slug_target__)).filter(
                        getattr(Model, cls.__slug_target__).like(pattern)
                    )
                    if current_id is not None:
                        query = query.filter(Model.id != current_id)
                    existing = [row[0] for row in query.all()]

                    if base_slug in existing:
                        # Compute next suffix
                        suffixes = [0]
                        for existing_slug in existing:
                            if existing_slug == base_slug:
                                suffixes.append(0)
                            elif existing_slug.startswith(f"{base_slug}-"):
                                suffix = existing_slug[len(base_slug) + 1 :]
                                if suffix.isdigit():
                                    suffixes.append(int(suffix))
                        slug = f"{base_slug}-{max(suffixes) + 1}"

            # Assign only if slug field is currently empty
            if not getattr(target, cls.__slug_target__, None):
                setattr(target, cls.__slug_target__, slug)

        event.listen(cls, "before_insert", generate_slug)
        event.listen(cls, "before_update", generate_slug)


class UUIDMixin:
    """
    Provides a GUID/UUID primary key column named `id`.
    """

    @declared_attr
    def id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(
            GUID,
            primary_key=True,
            default=uuid.uuid4,
            info={"label": _("ID")},
        )


class TimeStampMixin:
    """
    Adds created_at & updated_at timestamp columns.
    """

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
            info={"label": _("Created at")},
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
            info={"label": _("Updated at")},
        )


class BaseModel(AsyncAttrs, DeclarativeBase):
    """Asynchronous SQLAlchemy declarative base."""

    __allow_unmapped__ = True


class Base(BaseModel, UUIDMixin, TimeStampMixin):
    """
    Abstract base model including:
      - GUID primary key
      - created_at & updated_at timestamps
    """

    __abstract__ = True
