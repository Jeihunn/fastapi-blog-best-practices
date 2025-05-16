import io
import logging
from typing import Any, ClassVar, Dict, List, Tuple, cast

from fastapi import UploadFile
from sqladmin import ModelView
from starlette.datastructures import FormData
from starlette.datastructures import UploadFile as StarletteUploadFile
from starlette.requests import Request
from starlette_babel import gettext_lazy as _

from src.common.utils.file_helpers import validate_content_type
from src.core.config import settings
from src.core.storage import get_storage

logger = logging.getLogger(__name__)


class FileUploadMixin(ModelView):
    """
    Handle upload & cleanup for columns with info["file"]=True.
    Requires info["upload_to"]; supports optional allowed_types, max_size, namer.
    """

    model: ClassVar[type]

    async def on_model_change(
        self, data: Dict[str, Any], model: Any, is_created: bool, request: Request
    ) -> None:
        # Call parent hook first
        await super().on_model_change(data, model, is_created, request)
        storage = get_storage()

        for column in self.model.__table__.columns:  # type: ignore[attr-defined]
            if not column.info.get("file"):
                continue

            field_name = column.key
            upload_obj = data.pop(field_name, None)
            existing_path = getattr(model, field_name, None)

            # CLEAR: user ticked “clear” checkbox
            if isinstance(upload_obj, StarletteUploadFile) and not upload_obj.filename:
                if existing_path and settings.FILE_CLEANUP_ENABLED:
                    try:
                        await storage.delete(existing_path)
                    except Exception as exc:
                        logger.error(
                            "Error deleting old file for %s: %s", field_name, exc
                        )
                data[field_name] = None
                continue

            # NEW UPLOAD
            if isinstance(upload_obj, StarletteUploadFile) and upload_obj.filename:
                fastapi_file = cast(UploadFile, upload_obj)

                # 1) Validate content type if provided
                if allowed := column.info.get("allowed_types"):
                    validate_content_type(fastapi_file, allowed)

                # 2) Delete old file if cleanup enabled
                if existing_path and settings.FILE_CLEANUP_ENABLED:
                    try:
                        await storage.delete(existing_path)
                    except Exception as exc:
                        logger.error(
                            "Error deleting previous file for %s: %s", field_name, exc
                        )

                # 3) Determine upload destination
                upload_to = column.info.get("upload_to")
                if not upload_to:
                    logger.critical(
                        "Missing 'upload_to' for file field: %s", field_name
                    )
                    raise ValueError(
                        _("No upload_to defined for file field '%(field)s'")
                        % {"field": field_name}
                    )

                # 4) Collect extra upload parameters
                upload_params: Dict[str, Any] = {}
                if namer := column.info.get("namer"):
                    upload_params["namer"] = namer
                if max_size := column.info.get("max_size"):
                    upload_params["max_size"] = max_size

                # 5) Perform upload
                try:
                    result = await storage.upload(
                        fastapi_file, upload_to=upload_to, **upload_params
                    )
                    data[field_name] = result.get("db_path")
                except Exception as exc:
                    logger.error("Error uploading file for %s: %s", field_name, exc)
                    raise

    async def on_model_delete(self, model: Any, request: Request) -> None:
        # Skip if cleanup globally disabled
        if not settings.FILE_CLEANUP_ENABLED:
            return

        storage = get_storage()
        for column in self.model.__table__.columns:  # type: ignore[attr-defined]
            if not column.info.get("file"):
                continue

            field_name = column.key
            file_path = getattr(model, field_name, None)
            if not file_path:
                continue

            try:
                await storage.delete(file_path)
            except Exception as exc:
                logger.error(
                    "Error deleting file for %s during model deletion: %s",
                    field_name,
                    exc,
                )


async def patched_handle_form_data(
    self: ModelView,
    request: Request,
    obj: Any = None,
) -> FormData:
    """
    Override SQLAdmin's default form-data handling so that:
      - Only columns marked with info["file"]=True are considered for file logic.
      - If the clear-checkbox is checked, produce an empty UploadFile to trigger deletion.
      - If a new file is uploaded, pass it through.
      - Otherwise, skip the file field altogether to preserve existing path.
    """
    form = await request.form()
    items: List[Tuple[str, Any]] = []

    # Retrieve the current ModelView and its table metadata
    mv: ModelView = self._find_model_view(request.path_params["identity"])  # type: ignore[attr-defined]
    table = mv.model.__table__  # type: ignore[attr-defined]

    for key, value in form.multi_items():
        # Check if this field corresponds to a file-column
        column = table.columns.get(key)
        if (
            column is not None
            and column.info.get("file")
            and isinstance(value, StarletteUploadFile)
        ):
            # 1) Clear request: checkbox present
            if form.get(f"{key}_checkbox"):
                items.append((key, StarletteUploadFile(io.BytesIO(b""))))
                continue
            # 2) New upload: filename is non-empty
            if value.filename:
                items.append((key, value))
                continue
            # 3) Neither clear nor new file: skip to keep existing file path
            continue

        # All other form fields are appended normally
        items.append((key, value))

    return FormData(items)
