from pydantic import BaseModel, EmailStr, Field

from src.common.utils.types import E164PhoneNumber


class ContactCreate(BaseModel):
    phone_number: E164PhoneNumber = Field(
        ...,
        description="Phone number",
        json_schema_extra={"example": "+994123456789"},
    )
    email: EmailStr = Field(
        ...,
        description="Email address",
        json_schema_extra={"example": "user@example.com"},
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Your name",
        json_schema_extra={"example": "John Doe"},
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Write a message",
        json_schema_extra={"example": "Hi, I’d like to get in touch about…"},
    )
