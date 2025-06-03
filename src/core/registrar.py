import types
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import redis.asyncio as redis
from fastapi import FastAPI, Request, Response
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_limiter import FastAPILimiter
from fastapi_pagination import add_pagination
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette_babel import LocaleMiddleware, TimezoneMiddleware, get_translator
from starlette_babel.contrib.jinja import configure_jinja_env

from src.auth.admin import admin_auth
from src.blogs.admin import register_blogs_admin_views
from src.common.admin.application import MyAdmin
from src.common.admin.file_upload import patched_handle_form_data
from src.common.admin.formatters import register_admin_formatters
from src.common.errors.validation import register_validation_handlers
from src.common.jinja import register_jinja
from src.common.patches import apply_patches
from src.common.templates import templates
from src.core import path_conf
from src.core.config import settings
from src.core.database import engine
from src.core.logging import setup_logging
from src.essentials.admin import register_essentials_admin_views
from src.users.admin import register_users_admin_views


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    redis_connection = redis.from_url(  # type: ignore[no-untyped-call]
        settings.REDIS_URL, encoding="utf8", decode_responses=True
    )
    await FastAPILimiter.init(redis=redis_connection)

    yield

    await FastAPILimiter.close()


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance.
    """
    # Apply monkey-patches
    apply_patches()

    # Create the FastAPI instance
    app = FastAPI(
        debug=settings.DEBUG,
        title=settings.FASTAPI_TITLE,
        summary=settings.FASTAPI_SUMMARY,
        description=settings.FASTAPI_DESCRIPTION,
        version=settings.FASTAPI_VERSION,
        openapi_url=settings.FASTAPI_OPENAPI_URL,
        docs_url=settings.FASTAPI_DOCS_URL,
        redoc_url=settings.FASTAPI_REDOC_URL,
        lifespan=lifespan,
        terms_of_service=settings.FASTAPI_TERMS_OF_SERVICE,
        contact=settings.FASTAPI_CONTACT,
        license_info=settings.FASTAPI_LICENSE_INFO,
        swagger_ui_parameters={
            "docExpansion": "list",
            "deepLinking": True,
            "tagsSorter": "alpha",
            "operationsSorter": "alpha",
            "filter": True,
            "displayRequestDuration": True,
            "showCommonExtensions": True,
        },
    )

    # Register application components
    register_logging()
    register_i18n(app)
    register_middleware(app)
    register_assets(app)
    register_exception_handlers(app)
    register_validation_handlers(app)
    register_admin(app)
    register_router(app)
    register_pagination(app)

    return app


def register_logging() -> None:
    """
    Configure application logging settings.
    """
    setup_logging()


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def not_found_handler(
        request: Request, exc: StarletteHTTPException
    ) -> Response:
        """
        Handle 404 for non-API requests by rendering a custom template,
        otherwise fall back to FastAPI's default HTTP exception handler.
        """
        is_api = request.url.path.startswith("/api/")
        if exc.status_code == 404 and not is_api:
            # Return a Jinja2-rendered HTML page for 404 errors
            return templates.TemplateResponse(
                "frontend/404.html", {"request": request}, status_code=404
            )
        # Delegate to the built-in exception handler for other cases
        return await http_exception_handler(request, exc)


def register_assets(app: FastAPI) -> None:
    """
    Ensure the static/media dirs exist and mount them on the app."
    """
    # Static files
    path_conf.STATIC_DIR.mkdir(parents=True, exist_ok=True)
    app.mount(
        path_conf.STATIC_URL,
        StaticFiles(directory=str(path_conf.STATIC_DIR)),
        name="static",
    )

    # Media files
    path_conf.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    app.mount(
        path_conf.MEDIA_URL,
        StaticFiles(directory=str(path_conf.MEDIA_DIR)),
        name="media",
    )


def register_i18n(app: FastAPI) -> None:
    """
    Load translation files.
    """
    translator = get_translator()
    translator.load_from_directories([str(path_conf.LOCALES_DIR)])


def register_admin(app: FastAPI) -> None:
    """
    Initialize the SQLAdmin interface and apply custom file upload handling.
    """
    admin = MyAdmin(
        app,
        engine,
        base_url=settings.ADMIN_BASE_URL,
        title=settings.ADMIN_TITLE,
        logo_url=settings.ADMIN_LOGO_URL,
        favicon_url=settings.ADMIN_FAVICON_URL,
        debug=settings.DEBUG,
        templates_dir=str(path_conf.TEMPLATE_DIR),
        authentication_backend=admin_auth,
    )
    configure_jinja_env(admin.templates.env)
    register_jinja(admin.templates.env)
    admin._handle_form_data = types.MethodType(  # type: ignore[method-assign]
        patched_handle_form_data, admin
    )

    # Register custom formatters
    register_admin_formatters()

    # Register custom admin views
    register_users_admin_views(admin)
    register_blogs_admin_views(admin)
    register_essentials_admin_views(admin)


def register_middleware(app: FastAPI) -> None:
    """
    Include and configure global middleware.
    """
    # Trusted Host validation (Host header protection)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )

    # CORS (Cross-Origin Resource Sharing) settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOWED_ORIGINS,
        allow_origin_regex=settings.CORS_ALLOWED_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Internationalization & Timezone support
    app.add_middleware(
        LocaleMiddleware,
        locales=settings.SUPPORTED_LOCALES,
        default_locale=settings.DEFAULT_LOCALE,
    )
    app.add_middleware(TimezoneMiddleware, fallback=settings.TIME_ZONE)


def register_pagination(app: FastAPI) -> None:
    """
    Enable fastapi-pagination for all routers.
    """
    add_pagination(app)


def register_router(app: FastAPI) -> None:
    """
    Include all router modules.
    """
    register_api_router(app)
    register_web_router(app)


def register_api_router(app: FastAPI) -> None:
    """
    Include API router modules.
    """
    from src.auth.api.router import router as auth_api_router
    from src.blogs.api.router import router as blogs_api_router
    from src.essentials.api.router import router as essentials_api_router
    from src.healthcheck import router as healthcheck_router
    from src.users.api.router import router as users_api_router

    app.include_router(auth_api_router)
    app.include_router(blogs_api_router)
    app.include_router(essentials_api_router)
    app.include_router(healthcheck_router)
    app.include_router(users_api_router)


def register_web_router(app: FastAPI) -> None:
    """
    Include web router modules.
    """
    from src.auth.web.router import router as auth_web_router
    from src.blogs.web.router import router as blogs_web_router
    from src.essentials.web.router import router as essentials_web_router
    from src.users.web.router import router as users_web_router

    app.include_router(auth_web_router)
    app.include_router(blogs_web_router)
    app.include_router(essentials_web_router)
    app.include_router(users_web_router)
