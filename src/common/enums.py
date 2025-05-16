from enum import Enum


class EnvironmentStrategy(str, Enum):
    """
    Enum defining available environment strategies.
    """

    LOCAL = "local"
    PRODUCTION = "production"


class StorageBackendStrategy(str, Enum):
    """
    Enum defining available storage backend strategies.
    Extend this enum when adding new backends (e.g. S3, GCS).
    """

    LOCAL = "local"
