import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from urllib.parse import urlparse

from fastapi import UploadFile
from starlette_babel.translator import gettext

from src.common import exceptions as common_exceptions

# allow only ASCII letters, digits, underscore and hyphen
_filename_re = re.compile(r"[^A-Za-z0-9_-]+")


def secure_filename(file: UploadFile, prefix: str = "") -> str:
    """
    Generate a new filename by appending a UTC timestamp.

    Args:
        file (UploadFile): the uploaded file.
        prefix (str): optional prefix to prepend to the filename.

    Returns:
        str: a filename in the format '[prefix_]stem_timestamp.ext'.
    """
    filename = file.filename
    if filename is None:
        raise ValueError("Uploaded file has no filename")

    original = Path(filename)
    stem = original.stem
    extension = original.suffix.lower()

    # normalize accents and drop non-ASCII characters
    normalized = unicodedata.normalize("NFKD", stem)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    safe_stem = _filename_re.sub("_", ascii_only).strip("_")

    # append UTC timestamp
    timestamp = int(datetime.now(timezone.utc).timestamp())
    parts: List[str] = [part for part in (prefix, safe_stem, str(timestamp)) if part]
    return "_".join(parts) + extension


def get_public_url(value: str) -> str:
    """
    Serialize a file path into a publicly accessible URL.

    - Returns empty string if value is falsy.
    - Returns the value unchanged if it's already an absolute URL.
    - Otherwise delegates URL construction to the configured storage backend.
    """
    from src.core.storage import get_storage

    if not value:
        return value

    # If it"s already a valid URL, return as-is
    parsed = urlparse(value)
    if parsed.scheme and parsed.netloc:
        return value

    # Otherwise, delegate to the configured storage backend
    storage = get_storage()
    return storage.get_url(value)


def human_readable_size(size: int) -> str:
    """
    Convert bytes to a human-readable string (up to PB), trimming unnecessary zeros.
    """
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if size < 1024:
            break
        value = size / 1024
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return f"{text}{unit}"


def validate_content_type(file: UploadFile, allowed_types: List[str]) -> None:
    """
    Raise UnsupportedMediaTypeError if the file's MIME type is not in allowed_types.
    """
    if file.content_type not in allowed_types:
        msg = gettext("Unsupported file type: %(type)s. Allowed types: %(allowed)s") % {
            "type": file.content_type,
            "allowed": ", ".join(allowed_types),
        }
        raise common_exceptions.UnsupportedMediaTypeError(msg)
