# RUTA: app/routers/call_center/callcenter_lookup.py
# FECHA: 2026-07-25

from typing import Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.services.call_center.call_center_service import CallCenterService
from app.core.template_loader import jinja as templates

router = APIRouter(prefix="/call_center", tags=["Call Center Lookup"])

@router.get("/lookup/{customer_id}", response_class=HTMLResponse)
def lookup_page(request: Request, customer_id: int, next: Optional[str] = None, db: Session = Depends(get_db)):
    service = CallCenterService(db)
    
    # Obtenemos datos del cliente y su historial
    customer = service.get_customer_details(customer_id)
    history = service.get_customer_history(customer_id)
    
    # ⭐ Ordenar facturas
    invoices_list = history.get("invoices", [])
    if invoices_list:
        invoices_list = sorted(
            invoices_list,
            key=lambda x: (str(x.time_created or ''), x.id if hasattr(x, 'id') else 0),
            reverse=True
        )

    # ⭐ Ordenar estimados
    estimates_list = history.get("estimates", [])
    if estimates_list:
        estimates_list = sorted(
            estimates_list,
            key=lambda x: (str(x[0].estimated_appointment_date or ''), x[0].id),
            reverse=True
        )

    # ⭐ LÓGICA FINAL DE BACK_URL
    role = request.session.get("role")

    if next:
        # Manager SIEMPRE regresa a lo que lo llamó
        back_url = next
    else:
        # Si no viene next, decidir por rol
        if role == "sales":  # Call Center
            back_url = "/call_center/search"
        else:
            # Manager u otros → Customer Catalog
            back_url = "/customers/list"

    return templates.TemplateResponse(
        request=request,
        name="call_center/call_center_lookup.html",
        context={
            "request": request,
            "customer": customer,
            "invoices": invoices_list,
            "estimates": estimates_list,
            "back_url": back_url,
            "next": next
        }
    )

# Nuevo endpoint para obtener los detalles del estimado
@router.get("/estimates/details/{estimate_id}")
def get_estimate_details(estimate_id: int, db: Session = Depends(get_db)):
    service = CallCenterService(db)
    details = service.get_estimate_details(estimate_id)
    
    return [dict(row._mapping) for row in details]
