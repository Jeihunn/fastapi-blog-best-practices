from sqladmin import Admin
from sqladmin.authentication import login_required
from sqlalchemy import func, select
from starlette.requests import Request
from starlette.responses import Response

from src.blogs.models import BlogPost
from src.core.database import async_session_maker
from src.essentials.models import Contact
from src.users.models import User


class MyAdmin(Admin):
    """
    Custom Admin class with an embedded dashboard in the index route.
    """

    @login_required
    async def index(self, request: Request) -> Response:
        """Index route which can be overridden to create dashboards."""

        async with async_session_maker() as session:
            total_users = await session.scalar(select(func.count()).select_from(User))
            total_superusers = await session.scalar(
                select(func.count())
                .select_from(User)
                .where(User.is_superuser)  # type: ignore[arg-type]
            )
            total_posts = await session.scalar(
                select(func.count()).select_from(BlogPost)
            )
            total_published_posts = await session.scalar(
                select(func.count()).select_from(BlogPost).where(BlogPost.is_published)
            )
            total_contacts = await session.scalar(
                select(func.count()).select_from(Contact)
            )
            latest_contact = await session.scalar(
                select(Contact.created_at).order_by(Contact.created_at.desc()).limit(1)
            )

        context = {
            "metrics": {
                "total_users": total_users or 0,
                "total_superusers": total_superusers or 0,
                "total_posts": total_posts or 0,
                "total_published_posts": total_published_posts or 0,
                "total_contacts": total_contacts or 0,
                "latest_contact": latest_contact,
            }
        }

        return await self.templates.TemplateResponse(
            request,
            "sqladmin/index.html",
            context,
        )
