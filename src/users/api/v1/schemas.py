import uuid
from datetime import datetime
from typing import Optional

from fastapi_users import schemas
from pydantic import BaseModel, Field

from src.common.utils.types import FileUrl


class UserRead(schemas.BaseUser[uuid.UUID]):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_image: Optional[FileUrl] = None
    date_joined: datetime
    last_login: Optional[datetime] = None
    updated_at: datetime


class UserCreate(schemas.BaseUserCreate):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)


class UserUpdate(schemas.CreateUpdateDictModel):
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(
        ...,
        description="Current password",
        json_schema_extra={"example": "OldP@ssw0rd!"},
    )
    new_password: str = Field(
        ..., description="New password", json_schema_extra={"example": "N3wP@ssw0rd!"}
    )
