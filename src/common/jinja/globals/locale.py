import jinja2

from src.core.config import settings


def register_locale_globals(jinja_env: jinja2.Environment) -> None:
    jinja_env.globals["supported_locales"] = settings.SUPPORTED_LOCALES
