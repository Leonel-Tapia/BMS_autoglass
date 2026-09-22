# RUTA: app/routers/call_center/callcenter_menu.py
# FECHA: 2026-07-15 17:00 MDT

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from app.core.template_loader import jinja as templates

router = APIRouter(prefix="/call_center", tags=["Call Center Menu"])


@router.get("/menu", response_class=HTMLResponse)
def call_center_menu(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="call_center/call_center_menu.html",
        context={"request": request}
    )


@router.get("/logout")
def call_center_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/auth/login", status_code=303)
