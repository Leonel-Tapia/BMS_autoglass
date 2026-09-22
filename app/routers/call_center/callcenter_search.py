# PATH: app/routers/call_center/callcenter_search.py | UPDATED: 2026-09-11 (has_geocode flag)

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.services.call_center.call_center_service import CallCenterService
from app.core.template_loader import jinja as templates

router = APIRouter(prefix="/call_center", tags=["Call Center Search"])

# --- 1. RUTA PARA BUSQUEDA DINAMICA (JSON) ---
@router.get("/search-json")
def search_json(name: str = "", phone: str = "", db: Session = Depends(get_db)):
    service = CallCenterService(db)
    customers = service.search_customers_dynamic(name, phone)
    
    return [
        {
            "id": c.id, 
            "name": c.name, 
            "phone": c.phone, 
            "mood": c.mood, 
            "address": c.address, 
            "city": c.city,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "has_geocode": (c.latitude is not None and c.longitude is not None)
        } for c in customers
    ]

# --- 2. RUTA ORIGINAL DE RENDERIZADO ---
@router.get("/search", response_class=HTMLResponse)
def search_page(request: Request, query: str = "", db: Session = Depends(get_db)):

    # 🔒 Validate session
    if "user_id" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)

    # 🔒 Validate role
    role = str(request.session.get("role", "")).strip().lower()
    if role != "sales":
        return RedirectResponse(url="/auth/login", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="call_center/callcenter_search.html",
        context={"request": request}
    )