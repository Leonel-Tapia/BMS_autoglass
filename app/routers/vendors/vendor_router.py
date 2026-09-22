# PATH: app/routers/vendors/vendor_router.py | UPDATED: 2026-07-20 21:47 MDT
# ============================================================
# RUTA: app/routers/vendors/vendor_router.py
# ACTUALIZADO: 2026-07-20 21:47 MDT
# DESCRIPCIÓN: Router para Vendors con soporte de listado,
#              creación, edición e historial de compras.
#              Incluye detección automática de días en
#              payment_terms → terms_days.
# ============================================================

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import re

from app.database.database import get_db
from app.models.vendors.vendor_model import Vendor
from app.models.purchases.purchase_model import PurchaseOrder

router = APIRouter(
    prefix="/vendors",
    tags=["vendors"]
)

templates = Jinja2Templates(directory="app/templates")


# ============================================================
# FUNCIÓN AUXILIAR: EXTRAER DÍAS DESDE payment_terms
# ============================================================
def extract_terms_days(payment_terms: str) -> int:
    """
    Extrae el primer número encontrado en payment_terms.
    Si no hay número, devuelve 0.
    """
    if not payment_terms:
        return 0

    match = re.search(r'\d+', payment_terms)
    return int(match.group()) if match else 0


# ============================================================
# 1. LISTADO DE PROVEEDORES (LIST VIEW) + PAGINACIÓN
# ============================================================
@router.get("/list", response_class=HTMLResponse)
async def vendor_list(request: Request, db: Session = Depends(get_db)):
    page = int(request.query_params.get("page", 1))
    per_page = 12
    offset = (page - 1) * per_page

    total_vendors = db.query(Vendor).count()

    vendors = (
        db.query(Vendor)
        .order_by(Vendor.vendor_name.asc())
        .offset(offset)
        .limit(per_page)
        .all()
    )

    total_pages = (total_vendors + per_page - 1) // per_page

    return templates.TemplateResponse(
        request=request,
        name="vendors/vendor_list.html",
        context={
            "title": "Vendor Management System",
            "vendors": vendors,
            "page": page,
            "total_pages": total_pages
        }
    )


# ============================================================
# 2. MOSTRAR FORMULARIO DE CREACIÓN (CREATE VIEW)
# ============================================================
@router.get("/create", response_class=HTMLResponse)
async def vendor_create_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="vendors/vendor_create.html",
        context={"title": "Add New Vendor"}
    )


# ============================================================
# 3. PROCESAR GUARDADO DE PROVEEDOR (SAVE ACTION)
# ============================================================
@router.post("/create")
async def vendor_create_save(
    vendor_name: str = Form(...),
    vendor_code: str = Form(None),
    contact_name: str = Form(None),
    contact_title: str = Form(None),
    email: str = Form(None),
    phone: str = Form(None),
    mobile: str = Form(None),
    address: str = Form(None),
    city: str = Form(None),
    state: str = Form(None),
    zip_code: str = Form(None),
    payment_terms: str = Form(None),
    status_active: str = Form("true"),
    db: Session = Depends(get_db)
):
    is_active_bool = status_active.lower() == "true"

    # 🔥 DETECTAR DÍAS AUTOMÁTICAMENTE
    terms_days = extract_terms_days(payment_terms)

    new_vendor = Vendor(
        vendor_name=vendor_name,
        vendor_code=vendor_code,
        contact_name=contact_name,
        contact_title=contact_title,
        email=email,
        phone=phone,
        mobile=mobile,
        address=address,
        city=city,
        state=state,
        zip_code=zip_code,
        payment_terms=payment_terms,
        terms_days=terms_days,
        is_active=is_active_bool
    )

    try:
        db.add(new_vendor)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"ERROR: [BMS] Database error: {str(e)}")

    return RedirectResponse(url="/vendors/list", status_code=303)


# ============================================================
# 4. MOSTRAR FORMULARIO DE EDICIÓN (EDIT VIEW - GET)
# ============================================================
@router.get("/edit/{vendor_id}", response_class=HTMLResponse)
async def vendor_edit_form(vendor_id: int, request: Request, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()

    if not vendor:
        return RedirectResponse(url="/vendors/list", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="vendors/vendor_edit.html",
        context={
            "title": f"Edit Vendor: {vendor.vendor_name}",
            "vendor": vendor
        }
    )


# ============================================================
# 5. PROCESAR ACTUALIZACIÓN DE PROVEEDOR (UPDATE ACTION)
# ============================================================
@router.post("/edit/{vendor_id}")
async def vendor_edit_save(
    vendor_id: int,
    vendor_name: str = Form(...),
    vendor_code: str = Form(None),
    tax_id: str = Form(None),
    contact_name: str = Form(None),
    contact_title: str = Form(None),
    email: str = Form(None),
    phone: str = Form(None),
    mobile: str = Form(None),
    payment_terms: str = Form(None),
    website: str = Form(None),
    address: str = Form(None),
    city: str = Form(None),
    state: str = Form(None),
    zip_code: str = Form(None),
    notes: str = Form(None),
    status_active: str = Form("false"),
    db: Session = Depends(get_db)
):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()

    if not vendor:
        return RedirectResponse(url="/vendors/list", status_code=303)

    vendor.vendor_name = vendor_name
    vendor.vendor_code = vendor_code
    vendor.tax_id = tax_id
    vendor.contact_name = contact_name
    vendor.contact_title = contact_title
    vendor.email = email
    vendor.phone = phone
    vendor.mobile = mobile
    vendor.payment_terms = payment_terms
    vendor.website = website
    vendor.address = address
    vendor.city = city
    vendor.state = state
    vendor.zip_code = zip_code
    vendor.notes = notes
    vendor.is_active = status_active.lower() == "true"

    # 🔥 DETECTAR DÍAS AUTOMÁTICAMENTE
    vendor.terms_days = extract_terms_days(payment_terms)

    db.commit()
    return RedirectResponse(url="/vendors/list", status_code=303)


# ============================================================
# 6. HISTORIAL DE ÓRDENES DE COMPRA (PO HISTORY)
# ============================================================
@router.get("/po-history/{vendor_id}", response_class=HTMLResponse)
async def vendor_po_history(vendor_id: int, request: Request, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()

    if not vendor:
        return RedirectResponse(url="/vendors/list", status_code=303)

    purchase_orders = (
        db.query(PurchaseOrder)
        .filter(PurchaseOrder.vendor_id == vendor_id)
        .order_by(PurchaseOrder.po_number.desc())
        .all()
    )

    # ============================
    # ✔️ CÁLCULOS CORREGIDOS
    # ============================
    total_accepted = sum(po.grand_total for po in purchase_orders if po.status == "ACCEPTED")
    total_received = sum(po.grand_total for po in purchase_orders if po.status == "RECEIVED")

    # ✔️ PENDING = suma de POs NO recibidos
    total_pending = sum(po.grand_total for po in purchase_orders if po.status != "RECEIVED")

    # ✔️ LIFETIME = suma de todos los POs
    total_lifetime = sum(po.grand_total for po in purchase_orders)

    response = templates.TemplateResponse(
        request=request,
        name="vendors/vendor_po_history.html",
        context={
            "title": f"PO History: {vendor.vendor_name}",
            "vendor": vendor,
            "purchase_orders": purchase_orders,
            "total_accepted": total_accepted,
            "total_received": total_received,
            "total_pending": total_pending,
            "total_lifetime": total_lifetime
        }
    )

    response.headers["Cache-Control"] = "no-store"
    return response