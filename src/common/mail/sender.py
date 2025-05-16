from typing import Any, Dict, List, Optional, Union

from fastapi_mail import FastMail, MessageSchema, MessageType, MultipartSubtypeEnum
from fastapi_mail.config import ConnectionConfig
from jinja2 import Environment, FileSystemLoader
from pydantic import EmailStr
from starlette.datastructures import UploadFile
from starlette_babel.contrib.jinja import configure_jinja_env

from src.core import path_conf
from src.core.config import settings


class BabelConnectionConfig(ConnectionConfig):
    def template_engine(self) -> Environment:
        """
        Return template environment
        """
        folder = self.TEMPLATE_FOLDER
        if not folder:
            raise ValueError(
                "Class initialization did not include a ``TEMPLATE_FOLDER`` ``PathLike`` object."
            )
        template_env = Environment(loader=FileSystemLoader(folder))
        configure_jinja_env(template_env)
        return template_env


conf = BabelConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    MAIL_FROM=settings.MAIL_FROM,
    TEMPLATE_FOLDER=path_conf.TEMPLATE_DIR,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

fm = FastMail(conf)


async def send_email(
    recipients: List[EmailStr],
    subtype: MessageType,
    multipart_subtype: MultipartSubtypeEnum = MultipartSubtypeEnum.mixed,
    attachments: List[Union[UploadFile, Dict[str, Any], str]] = [],
    subject: str = "",
    body: Optional[Union[str, List[Any]]] = None,
    alternative_body: Optional[str] = None,
    template_body: Optional[Union[List[Any], Dict[str, Any], str]] = None,
    cc: List[EmailStr] = [],
    bcc: List[EmailStr] = [],
    reply_to: List[EmailStr] = [],
    charset: str = "utf-8",
    headers: Optional[Dict[str, Any]] = None,
    template_name: Optional[str] = None,
) -> None:
    message = MessageSchema(
        recipients=recipients,
        attachments=attachments,
        subject=subject,
        body=body,
        alternative_body=alternative_body,
        template_body=template_body,
        cc=cc,
        bcc=bcc,
        reply_to=reply_to,
        charset=charset,
        subtype=subtype,
        multipart_subtype=multipart_subtype,
        headers=headers,
    )
    await fm.send_message(message, template_name)
