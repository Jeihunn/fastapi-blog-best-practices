from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.common.utils.types import FileUrl


class TagRead(BaseModel):
    id: UUID
    name: str
    slug: str


class CategoryRead(BaseModel):
    id: UUID
    name: str
    slug: str


class AuthorRead(BaseModel):
    id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    profile_image: Optional[FileUrl]


class BlogPostRead(BaseModel):
    id: UUID
    title: str
    content: Optional[str]
    cover_image: FileUrl
    is_published: bool
    published_at: Optional[datetime]
    slug: str

    author: Optional[AuthorRead]
    tags: List[TagRead] = []
    categories: List[CategoryRead] = []

    likes_count: int
    comments_count: int

    model_config = ConfigDict(from_attributes=True)


class CommentRead(BaseModel):
    id: UUID
    content: str
    created_at: datetime
    updated_at: datetime
    blogpost_id: UUID

    user: AuthorRead


class CommentCreate(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Text content of the comment",
        examples=["I really enjoyed this article!"],
    )
