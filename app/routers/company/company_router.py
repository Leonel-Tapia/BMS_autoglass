# /app/routers/company/company_router.py - Updated: 2026-09-14 (origin_address)
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.company.company import Company 
from decimal import Decimal, InvalidOperation

router = APIRouter(prefix="/company", tags=["Company"])

# Helper para procesar campos numéricos decimales de forma segura
def parse_decimal(value: str) -> Decimal:
    if not value or value.strip() == "":
        return Decimal("0.00")
    try:
        return Decimal(value.replace(",", "."))
    except (InvalidOperation, ValueError):
        return Decimal("0.00")

# -----------------------------
# GET: Formulario de Creación
# -----------------------------
@router.get("/create", response_class=HTMLResponse)
def company_create_form(request: Request, db: Session = Depends(get_db)):

    existing = db.query(Company).first()
    if existing:
        return RedirectResponse(url="/company/detail", status_code=303)

    try:
        with open("app/templates/company/company_create.html", "r", encoding="utf-8") as f:
            html = f.read()

        html = html.replace("{{mode}}", "create")
        html = html.replace("{{title}}", "Register New Company")
        html = html.replace("{{form_action}}", "/company/create")

        placeholders = [
            "trade_name", "legal_name", "tax_id", "business_line", "address",
            "neighborhood", "city", "state", "postal_code", "main_phone",
            "main_email", "contact_name", "contact_phone", "contact_email",
            "notes", "invoice_notice", "general_sales_tax",
            "mobile_fee", "labor_cost", "materials_cost", "misc_cost",
            "origin_address"
        ]

        for field in placeholders:
            html = html.replace(f"{{{{{field}}}}}", "")

        html = html.replace("{{is_active_checked}}", "checked")

        return HTMLResponse(content=html)

    except FileNotFoundError:
        return HTMLResponse("<h3>Error: Template company_create.html no encontrado.</h3>", status_code=404)

# -----------------------------
# POST: Guardar Empresa
# -----------------------------
@router.post("/create")
def company_create(
    db: Session = Depends(get_db),
    trade_name: str = Form(...),
    legal_name: str = Form(...),
    tax_id: str = Form(None),
    business_line: str = Form(None),
    address: str = Form(None),
    neighborhood: str = Form(None),
    city: str = Form(None),
    state: str = Form(None),
    postal_code: str = Form(None),
    main_phone: str = Form(None),
    main_email: str = Form(None),
    contact_name: str = Form(None),
    contact_phone: str = Form(None),
    contact_email: str = Form(None),
    notes: str = Form(None),
    invoice_notice: str = Form(None),
    is_active: str = Form(None),
    general_sales_tax: str = Form(None),
    mobile_fee: str = Form(None),
    labor_cost: str = Form(None),
    materials_cost: str = Form(None),
    misc_cost: str = Form(None),
    origin_address: str = Form(None),
):

    active_bool = True if is_active is not None else False

    new_company = Company(
        trade_name=trade_name,
        legal_name=legal_name,
        tax_id=tax_id,
        business_line=business_line,
        address=address,
        neighborhood=neighborhood,
        city=city,
        state=state,
        postal_code=postal_code,
        main_phone=main_phone,
        main_email=main_email,
        contact_name=contact_name,
        contact_phone=contact_phone,
        contact_email=contact_email,
        notes=notes,
        invoice_notice=invoice_notice,
        is_active=active_bool,
        general_sales_tax=parse_decimal(general_sales_tax),
        mobile_fee=parse_decimal(mobile_fee),
        labor_cost=parse_decimal(labor_cost),
        materials_cost=parse_decimal(materials_cost),
        misc_cost=parse_decimal(misc_cost),
        origin_address=origin_address.strip() if origin_address and origin_address.strip() else None
    )

    try:
        db.add(new_company)
        db.commit()
        db.refresh(new_company)
        return RedirectResponse(url="/company/detail", status_code=303)
    except Exception as e:
        db.rollback()
        return HTMLResponse(f"<h3>Error al guardar en DB: {str(e)}</h3>", status_code=500)

# -----------------------------
# POST: Actualizar Empresa
# -----------------------------
@router.post("/update")
def company_update(
    db: Session = Depends(get_db),
    trade_name: str = Form(...),
    legal_name: str = Form(...),
    tax_id: str = Form(None),
    business_line: str = Form(None),
    address: str = Form(None),
    neighborhood: str = Form(None),
    city: str = Form(None),
    state: str = Form(None),
    postal_code: str = Form(None),
    main_phone: str = Form(None),
    main_email: str = Form(None),
    contact_name: str = Form(None),
    contact_phone: str = Form(None),
    contact_email: str = Form(None),
    notes: str = Form(None),
    invoice_notice: str = Form(None),
    is_active: str = Form(None),
    general_sales_tax: str = Form(None),
    mobile_fee: str = Form(None),
    labor_cost: str = Form(None),
    materials_cost: str = Form(None),
    misc_cost: str = Form(None),
    origin_address: str = Form(None),
):
    company = db.query(Company).first()
    if not company:
        return RedirectResponse(url="/company/create", status_code=303)

    company.trade_name = trade_name
    company.legal_name = legal_name
    company.tax_id = tax_id
    company.business_line = business_line
    company.address = address
    company.neighborhood = neighborhood
    company.city = city
    company.state = state
    company.postal_code = postal_code
    company.main_phone = main_phone
    company.main_email = main_email
    company.contact_name = contact_name
    company.contact_phone = contact_phone
    company.contact_email = contact_email
    company.notes = notes
    company.invoice_notice = invoice_notice
    company.is_active = True if is_active else False

    company.general_sales_tax = parse_decimal(general_sales_tax)
    company.mobile_fee = parse_decimal(mobile_fee)
    company.labor_cost = parse_decimal(labor_cost)
    company.materials_cost = parse_decimal(materials_cost)
    company.misc_cost = parse_decimal(misc_cost)

    # CAMBIO 2026-09-14: si viene vacío, guardar como NULL
    company.origin_address = origin_address.strip() if origin_address and origin_address.strip() else None

    db.commit()
    db.refresh(company)

    return RedirectResponse(url="/manager/menu", status_code=303)

# -----------------------------
# GET: Editar Empresa
# -----------------------------
@router.get("/edit", response_class=HTMLResponse)
def company_edit_form(request: Request, db: Session = Depends(get_db)):
    company = db.query(Company).first()

    if not company:
        return HTMLResponse("<h3>No hay empresa registrada. <a href='/company/create'>Registrar aquí</a></h3>")

    try:
        with open("app/templates/company/company_create.html", "r", encoding="utf-8") as f:
            html = f.read()

        replacements = {
            "{{mode}}": "edit",
            "{{title}}": f"Company: {company.trade_name}",
            "{{form_action}}": "/company/update",
            "{{trade_name}}": company.trade_name or "",
            "{{legal_name}}": company.legal_name or "",
            "{{tax_id}}": company.tax_id or "",
            "{{business_line}}": company.business_line or "",
            "{{address}}": company.address or "",
            "{{neighborhood}}": company.neighborhood or "",
            "{{city}}": company.city or "",
            "{{state}}": company.state or "",
            "{{postal_code}}": company.postal_code or "",
            "{{main_phone}}": company.main_phone or "",
            "{{main_email}}": company.main_email or "",
            "{{contact_name}}": company.contact_name or "",
            "{{contact_phone}}": company.contact_phone or "",
            "{{contact_email}}": company.contact_email or "",
            "{{notes}}": company.notes or "",
            "{{invoice_notice}}": company.invoice_notice or "",
            "{{general_sales_tax}}": company.general_sales_tax if company.general_sales_tax is not None else "0.00",
            "{{mobile_fee}}": company.mobile_fee if company.mobile_fee is not None else "0.00",
            "{{labor_cost}}": company.labor_cost if company.labor_cost is not None else "0.00",
            "{{materials_cost}}": company.materials_cost if company.materials_cost is not None else "0.00",
            "{{misc_cost}}": company.misc_cost if company.misc_cost is not None else "0.00",
            "{{origin_address}}": company.origin_address or "",
            "{{is_active_checked}}": "checked" if company.is_active else ""
        }

        for key, value in replacements.items():
            html = html.replace(key, str(value))

        return HTMLResponse(content=html)

    except FileNotFoundError:
        return HTMLResponse("<h3>Error: company_create.html no encontrado.</h3>", status_code=404)

# -----------------------------
# GET: Detalle de Empresa
# -----------------------------
@router.get("/detail", response_class=HTMLResponse)
def company_detail(request: Request, db: Session = Depends(get_db)):
    company = db.query(Company).first()

    if not company:
        return HTMLResponse("<h3>No hay empresa registrada. <a href='/company/create'>Registrar aquí</a></h3>")

    try:
        with open("app/templates/company/company_detail.html", "r", encoding="utf-8") as f:
            html = f.read()
        
        placeholders = {
            "{{trade_name}}": company.trade_name,
            "{{legal_name}}": company.legal_name,
            "{{tax_id}}": company.tax_id,
            "{{business_line}}": company.business_line,
            "{{address}}": company.address,
            "{{neighborhood}}": company.neighborhood,
            "{{city}}": company.city,
            "{{state}}": company.state,
            "{{postal_code}}": company.postal_code,
            "{{main_phone}}": company.main_phone,
            "{{main_email}}": company.main_email,
            "{{contact_name}}": company.contact_name,
            "{{contact_phone}}": company.contact_phone,
            "{{contact_email}}": company.contact_email,
            "{{notes}}": company.notes,
            "{{invoice_notice}}": company.invoice_notice,
            "{{is_active}}": "Activo" if company.is_active else "Inactivo",
            "{{general_sales_tax}}": f"{company.general_sales_tax}%",
            "{{mobile_fee}}": f"${company.mobile_fee}",
            "{{labor_cost}}": f"${company.labor_cost}",
            "{{materials_cost}}": f"${company.materials_cost}",
            "{{misc_cost}}": f"${company.misc_cost}",
            # CAMBIO 2026-09-14: valor con HTML si está vacío
            "{{origin_address}}": company.origin_address if company.origin_address else '<span style="color:#dc3545;font-style:italic;font-weight:bold;">Not configured — route optimization disabled</span>'
        }

        for key, value in placeholders.items():
            html = html.replace(key, str(value) if value is not None else "")

        return HTMLResponse(content=html)
    except FileNotFoundError:
        return HTMLResponse("<h3>Error: Plantilla de detalle no encontrada.</h3>", status_code=404)