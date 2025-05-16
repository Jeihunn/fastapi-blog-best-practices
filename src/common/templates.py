from fastapi.templating import Jinja2Templates
from starlette_babel.contrib.jinja import configure_jinja_env

from src.common.jinja import register_jinja
from src.core.path_conf import TEMPLATE_DIR

TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

configure_jinja_env(templates.env)
register_jinja(templates.env)
