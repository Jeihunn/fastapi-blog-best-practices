from datetime import datetime
from typing import Any, List, Optional, Sequence, cast
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination.links import Page
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.sql import ColumnElement
from starlette_babel.translator import gettext

from src.auth.fastapi_users import current_active_user
from src.blogs.api.v1.schemas import (
    BlogPostRead,
    CategoryRead,
    CommentCreate,
    CommentRead,
    TagRead,
)
from src.blogs.models import BlogLike, BlogPost, Category, Comment, Tag
from src.common.dependencies import get_async_session, ordering_dep
from src.users.models import User

router = APIRouter(prefix="/blogs")


@router.get(
    "/tags",
    response_model=List[TagRead],
    status_code=status.HTTP_200_OK,
    tags=["blogs (v1)"],
    summary="List all tags",
    description="Retrieve all available tags, ordered alphabetically.",
)
async def list_tags(
    session: AsyncSession = Depends(get_async_session),
) -> Sequence[Tag]:
    stmt = select(Tag).order_by(Tag.name)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get(
    "/categories",
    response_model=List[CategoryRead],
    status_code=status.HTTP_200_OK,
    tags=["blogs (v1)"],
    summary="List all categories",
    description="Retrieve all available categories, ordered alphabetically.",
)
async def list_categories(
    session: AsyncSession = Depends(get_async_session),
) -> Sequence[Category]:
    stmt = select(Category).order_by(Category.name)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get(
    "/",
    response_model=Page[BlogPostRead],
    status_code=status.HTTP_200_OK,
    tags=["blogs (v1)"],
    summary="List blog posts",
    description="Paginated list of published blogs with optional filters and ordering.",
)
async def list_blog_posts(
    session: AsyncSession = Depends(get_async_session),
    search: Optional[str] = Query(None, description="Search by title"),
    category_slug: Optional[str] = Query(None, description="Filter by category slug"),
    tag_slug: Optional[str] = Query(None, description="Filter by tag slug"),
    author_id: Optional[UUID] = Query(None, description="Filter by author ID"),
    published_from: Optional[datetime] = Query(
        None, description="Published on or after"
    ),
    published_to: Optional[datetime] = Query(
        None, description="Published on or before"
    ),
    order_clauses: List[ColumnElement[Any]] = Depends(
        ordering_dep(
            model=BlogPost,
            allowed_fields={"title", "published_at"},
        )
    ),
) -> Page[BlogPostRead]:
    # Filters
    filters: List[ColumnElement[Any]] = [BlogPost.is_published.is_(True)]
    if search:
        filters.append(BlogPost.title.ilike(f"%{search}%"))
    if category_slug:
        filters.append(BlogPost.categories.any(Category.slug == category_slug))
    if tag_slug:
        filters.append(BlogPost.tags.any(Tag.slug == tag_slug))
    if author_id:
        filters.append(BlogPost.author_id == author_id)
    if published_from:
        filters.append(BlogPost.published_at >= published_from)
    if published_to:
        filters.append(BlogPost.published_at <= published_to)

    # Base query
    stmt = (
        select(BlogPost)
        .options(
            joinedload(BlogPost.author),
            joinedload(BlogPost.tags),
            joinedload(BlogPost.categories),
            selectinload(BlogPost.likes),
            selectinload(BlogPost.comments),
        )
        .where(*filters)
    )

    # Ordering
    if order_clauses:
        stmt = stmt.order_by(*order_clauses)

    # Pagination
    return cast(Page[BlogPostRead], await paginate(session, stmt))


@router.get(
    "/{slug}",
    response_model=BlogPostRead,
    status_code=status.HTTP_200_OK,
    tags=["blogs (v1)"],
    summary="Get a single blog post",
    description="Retrieve a published blog post by its slug.",
)
async def get_blog_post(
    slug: str = Path(..., description="Slug of the blog post"),
    session: AsyncSession = Depends(get_async_session),
) -> BlogPost:
    stmt = (
        select(BlogPost)
        .options(
            joinedload(BlogPost.author),
            joinedload(BlogPost.tags),
            joinedload(BlogPost.categories),
            selectinload(BlogPost.likes),
            selectinload(BlogPost.comments),
        )
        .where(
            BlogPost.slug == slug,
            BlogPost.is_published.is_(True),
        )
    )
    result = await session.execute(stmt)
    post = result.scalars().first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=gettext("Blog post not found"),
        )
    return post


@router.get(
    "/{slug}/comments",
    response_model=Page[CommentRead],
    status_code=status.HTTP_200_OK,
    tags=["blogs (v1)"],
    summary="List comments for a blog post",
    description="Paginated list of comments for a given blog slug.",
)
async def list_comments(
    slug: str = Path(..., description="Slug of the blog post"),
    session: AsyncSession = Depends(get_async_session),
    order_clauses: List[ColumnElement[Any]] = Depends(
        ordering_dep(
            model=Comment,
            allowed_fields={"created_at"},
        )
    ),
) -> Page[CommentRead]:
    stmt = (
        select(Comment)
        .options(joinedload(Comment.user))
        .join(Comment.blogpost)
        .where(BlogPost.slug == slug)
    )
    if order_clauses:
        stmt = stmt.order_by(*order_clauses)
    return cast(Page[CommentRead], await paginate(session, stmt))


@router.post(
    "/{slug}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
    tags=["blogs (v1)"],
    summary="Create a comment for a blog post",
    description="Add a new comment to a published blog identified by its slug.",
)
async def create_comment(
    slug: str = Path(..., description="Slug of the blog post"),
    comment_in: CommentCreate = Body(..., description="New comment payload"),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> Comment:
    stmt = select(BlogPost).where(
        BlogPost.slug == slug,
        BlogPost.is_published.is_(True),
    )
    result = await session.execute(stmt)
    post = result.scalars().first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=gettext("Blog post not found"),
        )
    # Create comment
    new_comment = Comment(
        content=comment_in.content,
        user_id=current_user.id,
        blogpost_id=post.id,
    )
    session.add(new_comment)
    await session.commit()
    await session.refresh(new_comment)
    return new_comment


@router.post(
    "/{slug}/like",
    status_code=status.HTTP_201_CREATED,
    tags=["blogs (v1)"],
    summary="Like a blog post",
    description="Authenticated user likes the blog post.",
)
async def like_blog_post(
    slug: str = Path(..., description="Slug of the blog post"),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> None:
    # Fetch & verify post
    stmt = select(BlogPost).where(
        BlogPost.slug == slug,
        BlogPost.is_published.is_(True),
    )
    res = await session.execute(stmt)
    post = res.scalars().first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=gettext("Blog post not found"),
        )

    # Check if already liked
    like_stmt = select(BlogLike).where(
        BlogLike.user_id == current_user.id,
        BlogLike.blogpost_id == post.id,
    )
    like_res = await session.execute(like_stmt)
    if like_res.scalars().first():
        return  # already liked → no-op

    # Create & commit
    new_like = BlogLike(user_id=current_user.id, blogpost_id=post.id)
    session.add(new_like)
    await session.commit()


@router.delete(
    "/{slug}/like",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["blogs (v1)"],
    summary="Unlike a blog post",
    description="Authenticated user removes like from the blog post.",
)
async def unlike_blog_post(
    slug: str = Path(..., description="Slug of the blog post"),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> None:
    # Fetch & verify post
    stmt = select(BlogPost).where(
        BlogPost.slug == slug,
        BlogPost.is_published.is_(True),
    )
    res = await session.execute(stmt)
    post = res.scalars().first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=gettext("Blog post not found"),
        )

    # Find existing like
    like_stmt = select(BlogLike).where(
        BlogLike.user_id == current_user.id,
        BlogLike.blogpost_id == post.id,
    )
    like_res = await session.execute(like_stmt)
    existing = like_res.scalars().first()
    if not existing:
        return  # nothing to remove

    # Delete & commit
    await session.delete(existing)
    await session.commit()
