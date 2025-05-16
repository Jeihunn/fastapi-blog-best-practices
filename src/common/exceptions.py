class StorageException(Exception):
    """Base exception for storage-related errors."""

    pass


class StorageConfigurationError(StorageException):
    """Raised when the configured storage backend is unknown."""

    pass


class FileSizeLimitExceededError(StorageException):
    """Raised when an uploaded file exceeds the configured maximum size."""

    pass


class StorageUploadError(StorageException):
    """Raised for general upload failures."""

    pass


class UnsupportedMediaTypeError(StorageException):
    """Raised when the uploaded file’s MIME type is not allowed."""

    pass
