from pathlib import Path

# Project base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Logging directory
LOG_DIR = BASE_DIR / "logs"

# Templates directory
TEMPLATE_DIR = BASE_DIR / "templates"

# Static assets
STATIC_URL = "/static/"
STATIC_DIR = BASE_DIR / "static"

# Media files
MEDIA_URL = "/media/"
MEDIA_DIR = BASE_DIR / "media"

# Localization files
LOCALES_DIR = BASE_DIR / "locales"
