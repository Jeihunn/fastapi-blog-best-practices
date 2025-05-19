import logging

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette_babel.translator import gettext

from src.common.dependencies import get_async_session
from src.common.schemas import MessageResponse
from src.essentials.api.v1.schemas import ContactCreate
from src.essentials.models import Contact

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/essentials",
)


@router.post(
    "/contacts",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    tags=[
        "essentials (v1)",
    ],
    summary="Submit a new contact message",
    description="Create a new entry from the contact form.",
)
async def create_contact(
    payload: ContactCreate = Body(..., description="Contact form data"),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    contact = Contact(
        phone_number=payload.phone_number,
        email=payload.email,
        name=payload.name,
        message=payload.message,
    )

    try:
        session.add(contact)
        await session.commit()
    except Exception as exc:
        logger.error("Error creating contact: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=gettext("An error occurred while submitting your message."),
        )

    return {"message": gettext("Your message has been received.")}
