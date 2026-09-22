# ROUTE: /inventory/menu — FILE: inventory_menu_router.py — UPDATED: 2026-06-18 12:27 MDT

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/inventory", tags=["inventory"])
templates = Jinja2Templates(directory="app/templates")

# ============================
# INVENTORY MAIN MENU
# ============================
@router.get("/menu", response_class=HTMLResponse)
def inventory_menu(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="inventory/inventory_menu.html"
    )

# ============================
# INVENTORY CATALOG (NORMAL MODE)
# This view loads the simplified catalog without Manager features
# ============================
@router.get("/view/catalogo_inventory", response_class=HTMLResponse)
def inventory_catalog_normal(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="inventory/inventory_catalog_view.html"
    )
