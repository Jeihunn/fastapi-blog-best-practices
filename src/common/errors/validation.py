from typing import Any, Dict, List

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette_babel import gettext_lazy as _

from src.common.errors.messages import ERROR_TYPE_MESSAGES


def register_validation_handlers(app: FastAPI) -> None:
    """
    Add a handler for RequestValidationError to the FastAPI app.
    """

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        errors: List[Dict[str, Any]] = []
        for err in exc.errors():
            loc = err.get("loc", [])
            field = loc[-1] if loc else "default"
            error_type = err.get("type")
            ctx = err.get("ctx", {})

            translated_ctx = {
                key: _(value) if isinstance(value, str) else value
                for key, value in ctx.items()
            }

            field_map = ERROR_TYPE_MESSAGES.get(field, ERROR_TYPE_MESSAGES["default"])
            tmpl_info = field_map.get(error_type, {})
            msg_tmpl = tmpl_info.get("message")

            if msg_tmpl:
                try:
                    err["msg"] = msg_tmpl % translated_ctx
                except Exception:
                    err["msg"] = msg_tmpl
            errors.append(err)

        return JSONResponse(
            content={"detail": errors},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
