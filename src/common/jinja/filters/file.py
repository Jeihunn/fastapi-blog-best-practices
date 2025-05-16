import jinja2

from src.common.utils.file_helpers import get_public_url


def register_file_filters(jinja_env: jinja2.Environment) -> None:
    jinja_env.filters["public_url"] = get_public_url
