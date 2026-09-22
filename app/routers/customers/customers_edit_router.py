# /app/routers/customers/customers_edit_router.py | Updated: 2026-09-11 (auto-geocoding + status + next fix)
import re
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal

from app.database.database import get_db
from app.core.template_loader import jinja as templates
from app.models.customers.customer_model import Customer

# ===== GEOCODING =====
from app.utils.geocoding import geocode_address
# =====================


router = APIRouter(
    prefix="/customers",
    tags=["customers"]
)


# ============================================================
# 1. EDIT FORM VIEW (GET)
# ============================================================
@router.get("/edit/{customer_id}", response_class=HTMLResponse)
def customers_edit_form(
    request: Request,
    customer_id: int,
    origin: str = None,
    estimate_id: str = None,
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return RedirectResponse("/customers/list", status_code=303)

    # Normalizar next: si viene "None" como string, tratarlo como vacío
    raw_next = request.query_params.get("next")
    clean_next = None if raw_next in (None, "", "None") else raw_next

    return templates.TemplateResponse(
        request=request,
        name="customers/customers_edit.html",
        context={
            "customer": customer,
            "origin": origin,
            "estimate_id": estimate_id,
            "next": clean_next
        }
    )


# ============================================================
# 2. EDIT CUSTOMER (POST)
# ============================================================
@router.post("/edit/{customer_id}")
def customers_edit(
    customer_id: int,
    name: str = Form(...),
    business_name: str = Form(None),
    contact_name: str = Form(None),
    contact_phone: str = Form(None),
    contact_name2: str = Form(None),
    contact_phone2: str = Form(None),
    contact_relationship: str = Form(None),
    phone: str = Form(None),
    phone2: str = Form(None),
    email: str = Form(None),
    address: str = Form(None),
    city: str = Form(None),
    state: str = Form(None),
    zip_code: str = Form(None),
    tax_id: str = Form(None),
    language: str = Form(None),
    customer_type: str = Form(None),
    mood: str = Form(None),
    status: str = Form("ACTIVE"),
    internal_notes: str = Form(None),
    allow_sms: bool = Form(None),
    sms_opt_out_reason: str = Form(None),
    preferred_contact_method: str = Form(None),
    preferred_contact: str = Form(None),
    referral_source: str = Form(None),
    tags: str = Form(None),
    birthday: str = Form(None),
    last_purchase_date: str = Form(None),
    credit_limit: str = Form(None),
    customer_rating: str = Form(None),
    is_tax_exempt: bool = Form(None),
    tax_exempt: bool = Form(None),
    tax_exempt_license: str = Form(None),
    origin: str = Form(None),
    estimate_id: str = Form(None),
    next: str = Form(None),
    db: Session = Depends(get_db)
):

    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return RedirectResponse("/customers/list", status_code=303)

    # VALIDATE DUPLICATE PHONE
    if phone:
        phone_clean = re.sub(r'\D', '', phone)
        duplicate = db.query(Customer).filter(
            Customer.id != customer_id,
            Customer.phone_numeric == phone_clean
        ).first()
        
        if duplicate:
            print("[BMS WARNING] Duplicate phone detected")
            query_params = []
            if origin:
                query_params.append(f"origin={origin}")
            if estimate_id:
                query_params.append(f"estimate_id={estimate_id}")
            queryString = f"?{'&'.join(query_params)}" if query_params else ""
            return RedirectResponse(f"/customers/edit/{customer_id}{queryString}", status_code=303)

    # UPDATE MAIN FIELDS
    customer.name = name
    customer.business_name = business_name
    customer.contact_name = contact_name
    
    # TELEPHONES & NUMERICS (CLEANED)
    customer.contact_phone = contact_phone
    customer.contact_phone_numeric = re.sub(r'\D', '', contact_phone or "")
    customer.contact_name2 = contact_name2
    customer.contact_phone2 = contact_phone2
    customer.contact_phone2_numeric = re.sub(r'\D', '', contact_phone2 or "")
    customer.contact_relationship = contact_relationship
    customer.phone = phone
    customer.phone_numeric = re.sub(r'\D', '', phone or "")
    customer.phone2 = phone2
    customer.phone2_numeric = re.sub(r'\D', '', phone2 or "")
    
    customer.email = email
    customer.address = address
    customer.city = city
    customer.state = state
    customer.zip_code = zip_code
    customer.tax_id = tax_id
    customer.language = language
    customer.customer_type = customer_type
    customer.mood = mood
    customer.status = status
    customer.internal_notes = internal_notes

    # UPDATE ADDITIONAL INFORMATION
    customer.allow_sms = allow_sms
    customer.sms_opt_out_reason = sms_opt_out_reason
    customer.preferred_contact_method = preferred_contact_method
    customer.preferred_contact = preferred_contact
    customer.referral_source = referral_source
    customer.tags = tags

    customer.birthday = birthday if birthday else None
    customer.last_purchase_date = last_purchase_date if last_purchase_date else None

    # NUMERIC
    try:
        customer.credit_limit = Decimal(credit_limit) if credit_limit not in (None, "", "None") else Decimal("0.00")
    except:
        customer.credit_limit = Decimal("0.00")

    try:
        customer.customer_rating = int(customer_rating) if customer_rating and customer_rating.isdigit() else None
    except:
        customer.customer_rating = None

    # TAX FIELDS
    customer.is_tax_exempt = is_tax_exempt
    customer.tax_exempt = tax_exempt
    customer.tax_exempt_license = tax_exempt_license
    customer.updated_at = datetime.utcnow()

    # ===== GEOCODIFICACIÓN AUTOMÁTICA (RE-GEOCODE SI LA DIRECCIÓN CAMBIÓ) =====
    geocode_status = "skipped"
    if address and city and state:
        full_address = f"{address}, {city}, {state} {zip_code or ''}".strip()
        
        # Solo re-geocodificar si la dirección cambió o no hay coordenadas
        current_address = f"{customer.address or ''}, {customer.city or ''}, {customer.state or ''} {customer.zip_code or ''}".strip()
        needs_geocode = (
            customer.latitude is None or 
            customer.longitude is None or
            current_address != full_address
        )
        
        if needs_geocode:
            coords = geocode_address(full_address)
            if coords:
                customer.latitude = coords[0]
                customer.longitude = coords[1]
                geocode_status = "ok"
                print(f"[GEOCODE OK] '{name}' -> {coords}")
            else:
                geocode_status = "fail"
                print(f"[GEOCODE FAIL] '{name}' -> '{full_address}' (no encontrada)")
    # =========================================================================

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[BMS ERROR] {str(e)}")

    # REDIRECCIÓN LÓGICA FINAL
    if origin in ["estimate", "estimate_edit"]:
        if estimate_id == "new":
            return RedirectResponse(f"/estimates/new/{customer_id}?geocode={geocode_status}", status_code=303)
        return RedirectResponse(f"/estimates/edit/{estimate_id}?geocode={geocode_status}", status_code=303)

    # Si viene del Call Center, regresa de inmediato a su pantalla de lookup con el ID exacto
    if origin and ("call_center" in origin or "lookup" in origin):
        if next and next != "None":
            return RedirectResponse(f"/call_center/lookup/{customer_id}?next={next}&geocode={geocode_status}", status_code=303)
        return RedirectResponse(f"/call_center/lookup/{customer_id}?geocode={geocode_status}", status_code=303)

    return RedirectResponse(f"/customers/list?geocode={geocode_status}", status_code=303)