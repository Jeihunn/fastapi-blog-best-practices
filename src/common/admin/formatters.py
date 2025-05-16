from datetime import datetime

from sqladmin.formatters import BASE_FORMATTERS as SQLADMIN_BASE_FORMATTERS
from starlette_babel import format_datetime as babel_format_datetime


def datetime_formatter(value: datetime) -> str:
    return babel_format_datetime(value, format="long")


def register_admin_formatters() -> None:
    """Register custom formatters for SQLAdmin."""
    SQLADMIN_BASE_FORMATTERS[datetime] = datetime_formatter  # type: ignore[assignment]
