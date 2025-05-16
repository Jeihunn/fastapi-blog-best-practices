from typing import Any

from starlette_babel import gettext_lazy as _

ERROR_TYPE_MESSAGES: dict[str, dict[str, Any]] = {
    "email": {
        "value_error": {
            "message": _("value is not a valid email address: %(reason)s"),
            "reasons": [
                _("The part after the @-sign is not valid. It should have a period."),
                _("There must be something after the @-sign."),
                _("There must be something before the @-sign."),
            ],
        },
    },
    "phone_number": {
        "value_error": {
            "message": _("value is not a valid phone number"),
        },
    },
    "default": {
        "missing": {
            "message": _("Field required"),
        },
        "string_too_short": {
            "message": _("String should have at least %(min_length)d characters"),
        },
    },
}
