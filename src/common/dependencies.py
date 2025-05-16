from typing import Any, AsyncGenerator, List, Optional, Set, Type

from fastapi import HTTPException, Query, status
from sqlalchemy import asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from src.core.database import async_session_maker


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


def ordering_dep(
    model: Type[Any],
    allowed_fields: Set[str],
    param_name: str = "ordering",
    description: str = "Comma-separated sort fields; prefix '-' for descending.",
) -> Any:
    """
    Creates a FastAPI dependency that parses ?ordering=...
    into SQLAlchemy order_by clauses, enforcing allowed_fields.
    """
    allowed_list = ", ".join(f"<code>{f}</code>" for f in sorted(allowed_fields))
    full_description = f"{description}<br/><strong>Allowed:</strong> {allowed_list}"

    def dependency(
        ordering: Optional[str] = Query(
            None, alias=param_name, description=full_description
        )
    ) -> List[ColumnElement[Any]]:
        if not ordering:
            return []
        clauses: List[ColumnElement[Any]] = []
        for raw in ordering.split(","):
            raw = raw.strip()
            field = raw.lstrip("-")
            if field not in allowed_fields:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid ordering field: {field}",
                )
            column = getattr(model, field)
            clauses.append(desc(column) if raw.startswith("-") else asc(column))
        return clauses

    return dependency
