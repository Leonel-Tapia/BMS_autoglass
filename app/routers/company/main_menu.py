# /app/routers/company/main_menu.py | Updated: 2026-05-07
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

# 🔥 IMPORTACIÓN CORRECTA DEL LOADER
from app.core.template_loader import jinja as templates

router = APIRouter(prefix="/company", tags=["Main Menu"])

@router.get("/main_menu", response_class=HTMLResponse)
def get_main_menu(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="company/main_menu.html",
        context={}
    )
