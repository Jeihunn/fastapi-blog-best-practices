from typing import Annotated

from pydantic import PlainSerializer
from pydantic_extra_types.phone_numbers import PhoneNumber

from src.common.utils.file_helpers import get_public_url

FileUrl = Annotated[
    str,
    PlainSerializer(
        get_public_url,
        return_type=str,
    ),
]


class E164PhoneNumber(PhoneNumber):
    phone_format: str = "E164"
