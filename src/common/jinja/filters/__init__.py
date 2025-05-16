import jinja2

from src.common.jinja.filters.file import register_file_filters


def register_all_filters(jinja_env: jinja2.Environment) -> None:
    """
    Load all category-specific Jinja2 filters into the environment.
    """
    register_file_filters(jinja_env)
