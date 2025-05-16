import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from urllib.parse import urljoin

import aiofiles
from fastapi import UploadFile
from starlette_babel.translator import gettext

from src.common import exceptions as common_exceptions
from src.common.enums import StorageBackendStrategy
from src.common.utils.file_helpers import human_readable_size, secure_filename
from src.core import path_conf
from src.core.config import settings

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    @abstractmethod
    def get_url(self, path: str) -> str:
        """
        Given a relative file path, return a full public URL.
        Must be implemented by each storage backend.
        """

    @abstractmethod
    async def upload(
        self,
        file: UploadFile,
        upload_to: str,
        *,
        namer: Callable[[UploadFile], str] = secure_filename,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Upload a file to the backend.

        Args:
            file: The UploadFile instance.
            upload_to: Subdirectory or key prefix under which to store the file.
            namer: Callable to generate the filename (defaults to secure_filename).
            **kwargs: Backend-specific options (e.g. max_size, chunk_size).

        Returns:
            A dict with keys: filename, db_path, url.
        """

    @abstractmethod
    async def delete(self, path: str) -> None:
        """
        Delete a file given its stored path (db_path).
        """


class LocalStorage(StorageBackend):
    def get_url(self, path: str) -> str:
        """
        Build a URL for locally served media files.
        If MEDIA_BASE_URL is set, use it as the URL prefix.
        """
        if settings.MEDIA_BASE_URL:
            base = str(settings.MEDIA_BASE_URL).rstrip("/") + "/"
            return urljoin(base, path)

        backend_root = str(settings.BACKEND_URL).rstrip("/")
        media_route = path_conf.MEDIA_URL.strip("/")
        return urljoin(f"{backend_root}/{media_route}/", path)

    async def upload(
        self,
        file: UploadFile,
        upload_to: str,
        *,
        namer: Callable[[UploadFile], str] = secure_filename,
        max_size: Optional[int] = None,
        chunk_size: int = 64 * 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Write the incoming UploadFile to local disk under MEDIA_DIR/upload_to/,
        enforcing an optional size limit.
        """
        subdir = upload_to.strip("/")
        dest_dir = Path(path_conf.MEDIA_DIR) / subdir
        dest_dir.mkdir(parents=True, exist_ok=True)

        filename = namer(file)
        file_path = dest_dir / filename
        total = 0

        try:
            async with aiofiles.open(file_path, "wb") as buf:
                while chunk := await file.read(chunk_size):
                    total += len(chunk)
                    if max_size and total > max_size:
                        msg = gettext("File too large (%(actual)s > %(allowed)s)") % {
                            "actual": human_readable_size(total),
                            "allowed": human_readable_size(max_size),
                        }
                        raise common_exceptions.FileSizeLimitExceededError(msg)
                    await buf.write(chunk)
        except common_exceptions.FileSizeLimitExceededError:
            self._cleanup(file_path)
            raise
        except Exception as exc:
            self._cleanup(file_path)
            logger.error("Failed to upload file: %s", exc)
            raise common_exceptions.StorageUploadError(exc)
        finally:
            await file.close()

        db_path = f"{subdir}/{filename}"
        return {
            "filename": filename,
            "db_path": db_path,
            "url": self.get_url(db_path),
        }

    async def delete(self, path: str) -> None:
        """
        Delete a file from local storage by its db_path.
        """
        file_path = Path(path_conf.MEDIA_DIR) / path.lstrip("/")
        self._cleanup(file_path)

    def _cleanup(self, path: Path) -> None:
        """
        Helper to remove a partially written file on error.
        """
        try:
            if path.exists():
                path.unlink()
        except Exception as exc:
            logger.error("Failed to cleanup file: %s", exc)


# Future backends (S3, GCS) should subclass StorageBackend here
# class S3Storage(StorageBackend): ...

# Map each strategy to its implementation
_BACKENDS: dict[StorageBackendStrategy, StorageBackend] = {
    StorageBackendStrategy.LOCAL: LocalStorage(),
    # Future backends (S3, GCS) should be added here
}


def get_storage() -> StorageBackend:
    """
    Return the configured storage backend. Raises StorageConfigurationError if unknown.
    """
    backend_type = settings.STORAGE_BACKEND_STRATEGY
    try:
        return _BACKENDS[backend_type]
    except KeyError:
        supported = [e.value for e in StorageBackendStrategy]
        raise common_exceptions.StorageConfigurationError(
            f"Unknown storage backend: {backend_type!r}. Supported: {supported}"
        )
