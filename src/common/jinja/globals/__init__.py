import jinja2


def register_all_globals(jinja_env: jinja2.Environment) -> None:
    """
    Load all category-specific Jinja2 globals into the environment.
    """
    from src.common.jinja.globals.locale import register_locale_globals

    register_locale_globals(jinja_env)
