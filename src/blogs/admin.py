from typing import Any, cast

from markupsafe import Markup
from sqladmin import Admin, ModelView
from sqladmin.fields import FileField
from starlette_babel import gettext_lazy as _
from wtforms.validators import Optional

from src.blogs.models import BlogLike, BlogPost, Category, Comment, Tag
from src.common.admin.file_upload import FileUploadMixin
from src.common.utils.file_helpers import get_public_url


class CategoryAdmin(ModelView, model=Category):
    name = _("Category")
    name_plural = _("Categories")
    icon = "fa-solid fa-folder-open"
    category = _("Blog")

    column_labels = {
        "id": cast(str, Category.id.info.get("label")),
        "name": cast(str, Category.name.info.get("label")),
        "slug": cast(str, Category.slug.info.get("label")),
        "created_at": cast(str, Category.created_at.info.get("label")),
        "updated_at": cast(str, Category.updated_at.info.get("label")),
    }

    column_list = [
        "id",
        "name",
        "slug",
        "created_at",
        "updated_at",
    ]
    column_searchable_list = ["id", "name", "slug"]
    column_sortable_list = column_list
    column_default_sort = ("name", False)
    column_details_list = [
        "id",
        "name",
        "slug",
        "created_at",
        "updated_at",
    ]
    form_columns = [
        "name",
        "slug",
    ]
    form_args = {
        "slug": {
            "validators": [Optional()],
        }
    }
    form_widget_args = {
        "slug": {
            "required": False,
        }
    }


class TagAdmin(ModelView, model=Tag):
    name = _("Tag")
    name_plural = _("Tags")
    icon = "fa-solid fa-tag"
    category = _("Blog")

    column_labels = {
        "id": cast(str, Tag.id.info.get("label")),
        "name": cast(str, Tag.name.info.get("label")),
        "slug": cast(str, Tag.slug.info.get("label")),
        "created_at": cast(str, Tag.created_at.info.get("label")),
        "updated_at": cast(str, Tag.updated_at.info.get("label")),
    }

    column_list = [
        "id",
        "name",
        "slug",
        "created_at",
        "updated_at",
    ]
    column_searchable_list = ["id", "name", "slug"]
    column_sortable_list = column_list
    column_default_sort = ("name", False)
    column_details_list = [
        "id",
        "name",
        "slug",
        "created_at",
        "updated_at",
    ]
    form_columns = [
        "name",
        "slug",
    ]
    form_args = {
        "slug": {
            "validators": [Optional()],
        }
    }
    form_widget_args = {
        "slug": {
            "required": False,
        }
    }


class BlogPostAdmin(FileUploadMixin, model=BlogPost):
    name = _("Blog post")
    name_plural = _("Blog posts")
    icon = "fa-solid fa-newspaper"
    category = _("Blog")
    create_template = "admin/blogs/BlogAdmin/create.html"
    edit_template = "admin/blogs/BlogAdmin/edit.html"

    @staticmethod
    def _fmt_cover_image(model: Any, col: Any) -> Markup:
        if not model.cover_image:
            return Markup("")
        url = get_public_url(model.cover_image)
        return Markup(
            f'<img src="{url}" style="height:50px;object-fit:cover;border-radius:4px;" />'
        )

    column_labels = {
        "author_id": cast(str, BlogPost.author_id.info.get("label")),
        "id": cast(str, BlogPost.id.info.get("label")),
        "title": cast(str, BlogPost.title.info.get("label")),
        "content": cast(str, BlogPost.content.info.get("label")),
        "cover_image": cast(str, BlogPost.cover_image.info.get("label")),
        "is_published": cast(str, BlogPost.is_published.info.get("label")),
        "published_at": cast(str, BlogPost.published_at.info.get("label")),
        "slug": cast(str, BlogPost.slug.info.get("label")),
        "created_at": cast(str, BlogPost.created_at.info.get("label")),
        "updated_at": cast(str, BlogPost.updated_at.info.get("label")),
        "author": cast(str, BlogPost.author.info.get("label")),
        "categories": cast(str, BlogPost.categories.info.get("label")),
        "tags": cast(str, BlogPost.tags.info.get("label")),
        "comments": cast(str, BlogPost.comments.info.get("label")),
        "likes": cast(str, BlogPost.likes.info.get("label")),
        "likes_count": _("Likes count"),
        "comments_count": _("Comments count"),
    }

    column_list = [
        "id",
        "title",
        "cover_image",
        "author",
        "slug",
        "is_published",
        "published_at",
        "created_at",
        "updated_at",
    ]
    column_formatters = {
        "cover_image": _fmt_cover_image,
    }
    column_searchable_list = ["id", "title", "slug", "author_id"]
    column_sortable_list = [
        "id",
        "title",
        "cover_image",
        "slug",
        "is_published",
        "published_at",
        "created_at",
        "updated_at",
    ]
    column_default_sort = ("created_at", True)
    column_details_list = [
        "id",
        "title",
        "author",
        "categories",
        "tags",
        "content",
        "cover_image",
        "is_published",
        "published_at",
        "slug",
        "created_at",
        "updated_at",
        "likes_count",
        "comments_count",
    ]
    form_columns = [
        "title",
        "author",
        "categories",
        "tags",
        "content",
        "cover_image",
        "published_at",
        "is_published",
        "slug",
    ]
    form_overrides = {
        "cover_image": FileField,
    }
    form_args = {
        "slug": {
            "validators": [Optional()],
        },
        "cover_image": {
            "validators": [Optional()],
        },
    }
    form_widget_args = {
        "slug": {
            "required": False,
        },
        "cover_image": {
            "required": False,
        },
    }


class CommentAdmin(ModelView, model=Comment):
    name = _("Comment")
    name_plural = _("Comments")
    icon = "fa-solid fa-comment"
    category = _("Blog")

    column_labels = {
        "user_id": cast(str, Comment.user_id.info.get("label")),
        "blogpost_id": cast(str, Comment.blogpost_id.info.get("label")),
        "id": cast(str, Comment.id.info.get("label")),
        "content": cast(str, Comment.content.info.get("label")),
        "created_at": cast(str, Comment.created_at.info.get("label")),
        "updated_at": cast(str, Comment.updated_at.info.get("label")),
        "user": cast(str, Comment.user.info.get("label")),
        "blogpost": cast(str, Comment.blogpost.info.get("label")),
    }

    column_list = [
        "id",
        "user",
        "blogpost",
        "content",
        "created_at",
        "updated_at",
    ]
    column_searchable_list = ["id", "user_id", "blogpost_id", "content"]
    column_sortable_list = [
        "id",
        "content",
        "created_at",
        "updated_at",
    ]
    column_default_sort = ("created_at", True)
    column_details_list = [
        "id",
        "user",
        "blogpost",
        "content",
        "created_at",
        "updated_at",
    ]
    form_columns = [
        "user",
        "blogpost",
        "content",
    ]


class BlogLikeAdmin(ModelView, model=BlogLike):
    name = _("Blog like")
    name_plural = _("Blog likes")
    icon = "fa-solid fa-thumbs-up"
    category = _("Blog")

    column_labels = {
        "user_id": cast(str, BlogLike.user_id.info.get("label")),
        "blogpost_id": cast(str, BlogLike.blogpost_id.info.get("label")),
        "id": cast(str, BlogLike.id.info.get("label")),
        "created_at": cast(str, BlogLike.created_at.info.get("label")),
        "updated_at": cast(str, BlogLike.updated_at.info.get("label")),
        "user": cast(str, BlogLike.user.info.get("label")),
        "blogpost": cast(str, BlogLike.blogpost.info.get("label")),
    }

    column_list = [
        "id",
        "user",
        "blogpost",
        "created_at",
        "updated_at",
    ]
    column_searchable_list = ["user_id", "blogpost_id"]
    column_sortable_list = [
        "id",
        "created_at",
        "updated_at",
    ]
    column_default_sort = ("created_at", True)
    column_details_list = [
        "id",
        "user",
        "blogpost",
        "created_at",
        "updated_at",
    ]
    form_columns = [
        "user",
        "blogpost",
    ]


def register_blogs_admin_views(admin: Admin) -> None:
    admin.add_view(CategoryAdmin)
    admin.add_view(TagAdmin)
    admin.add_view(BlogPostAdmin)
    admin.add_view(CommentAdmin)
    admin.add_view(BlogLikeAdmin)
