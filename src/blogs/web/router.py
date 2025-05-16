from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from src.common.templates import templates

router = APIRouter()


@router.get("/blogs", name="blogs", include_in_schema=False)
def blogs(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("frontend/blogs.html", {"request": request})


@router.get(
    "/blogs/{slug}",
    name="blog_details",
    include_in_schema=False,
)
def blog_details(request: Request, slug: str) -> HTMLResponse:
    return templates.TemplateResponse(
        "frontend/blog-details.html",
        {
            "request": request,
            "slug": slug,
        },
    )
