import uuid

from fastapi_users_db_sqlalchemy.generics import GUID
from sqladmin.models import ModelView
from starlette_babel import LazyString


def patch_lazystring_hash() -> None:
    """
    Add a __hash__ method to LazyString.

    SQLAdmin inverts the `column_labels` mapping (value → key), which requires
    label values to be hashable. This prevents TypeError during that inversion.
    """
    LazyString.__hash__ = lambda self: hash(str(self))  # type: ignore[method-assign]


def patch_guid_python_type() -> None:
    """
    Ensure SQLAlchemyUserDatabase GUID columns map to uuid.UUID.

    This tells the generic GUID type to use Python’s built-in uuid.UUID for
    primary key columns.
    """
    GUID.impl.python_type = uuid.UUID


def patch_search_placeholder() -> None:
    """
    Override ModelView.search_placeholder to cast lazy labels to str.

    Prevents the “expected str instance, LazyString found” error when
    SQLAdmin renders the search placeholder.
    """

    def search_placeholder(self: ModelView) -> str:
        labels: list[str] = [
            str(self._column_labels.get(field, field)) for field in self._search_fields
        ]
        return ", ".join(labels)

    ModelView.search_placeholder = search_placeholder  # type: ignore[method-assign]


def apply_patches() -> None:
    """
    Apply all configured monkey-patches.

    Call this before creating your FastAPI app to ensure all
    third-party classes are patched appropriately.
    """
    patch_lazystring_hash()
    patch_guid_python_type()
    patch_search_placeholder()
