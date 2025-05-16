import jinja2

from src.common.jinja.filters import register_all_filters
from src.common.jinja.globals import register_all_globals

__all__ = ["register_jinja"]


def register_jinja(jinja_env: jinja2.Environment) -> None:
    register_all_globals(jinja_env)
    register_all_filters(jinja_env)
