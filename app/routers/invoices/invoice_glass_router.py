# /app/routers/invoices/invoice_glass_router.py
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import Optional
from app.database.database import get_db
from app.core.template_loader import jinja as templates

from app.models.invoices.invoice_model import Invoice, InvoiceItem
from app.models.invoices.invoice_glass_model import InvoiceGlass
from app.models.customers.customer_model import Customer
from app.models.inventory.year_model import Year


router = APIRouter(
    prefix="/invoices",
    tags=["invoice_glasses"]
)


# ============================================================
# 1. VIEW GLASS REGISTER PAGE (pantalla dedicada)
# ============================================================
@router.get("/{invoice_id}/glasses", response_class=HTMLResponse)
def view_invoice_glasses(
    invoice_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        return RedirectResponse("/invoices/workshop", status_code=303)

    customer = None
    if invoice.customer_id:
        customer = db.query(Customer).filter(Customer.id == invoice.customer_id).first()

    vehicle_year = None
    if invoice.vehicle_year_id:
        year_record = db.query(Year).filter(Year.id == invoice.vehicle_year_id).first()
        if year_record:
            vehicle_year = year_record.year

    glasses = db.query(InvoiceGlass).filter(
        InvoiceGlass.invoice_id == invoice_id
    ).order_by(desc(InvoiceGlass.created_at)).all()

    # NUEVO: items del invoice (para mostrar qué vidrio se necesita)
    invoice_items = db.query(InvoiceItem).filter(
        InvoiceItem.invoice_id == invoice_id
    ).all()

    user_role = request.session.get("role", "").strip().lower()

    return templates.TemplateResponse(
        request=request,
        name="invoices/invoice_glass_register.html",
        context={
            "invoice": invoice,
            "customer": customer,
            "vehicle_year": vehicle_year,
            "glasses": glasses,
            "invoice_items": invoice_items,
            "user_role": user_role
        }
    )


# ============================================================
# 2. CREATE GLASS (form submit → redirect)
# ============================================================
@router.post("/{invoice_id}/glasses")
def create_invoice_glass(
    invoice_id: int,
    request: Request,
    purchase_order_number: Optional[str] = Form(None),
    purchase_date: Optional[str] = Form(None),
    vendor: Optional[str] = Form(None),
    vendor_invoice_number: Optional[str] = Form(None),
    vendor_invoice_date: Optional[str] = Form(None),
    nags_code: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    glass_type: Optional[str] = Form(None),
    position: Optional[str] = Form(None),
    purchase_price: Optional[str] = Form(None),
    sales_price: Optional[str] = Form(None),
    payment_status: str = Form("PENDING"),
    is_ordered: Optional[str] = Form(None),
    status: str = Form("ORDERED"),
    storage_location: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    def parse_date(s):
        if not s:
            return None
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except ValueError:
            return None

    def parse_decimal(s):
        if s is None or s == "":
            return None
        try:
            return float(s)
        except ValueError:
            return None

    current_username = request.session.get("username") or "System"

    new_glass = InvoiceGlass(
        invoice_id=invoice_id,
        purchase_order_number=purchase_order_number or None,
        purchase_date=parse_date(purchase_date),
        vendor=vendor or None,
        vendor_invoice_number=vendor_invoice_number or None,
        vendor_invoice_date=parse_date(vendor_invoice_date),
        nags_code=nags_code or None,
        description=description or None,
        glass_type=glass_type or None,
        position=position or None,
        purchase_price=parse_decimal(purchase_price),
        sales_price=parse_decimal(sales_price),
        payment_status=payment_status or "PENDING",
        is_ordered=(str(is_ordered).lower() in ("on", "true", "1")),
        status=status or "ORDERED",
        storage_location=storage_location or None,
        notes=notes or None,
        created_by=current_username
    )

    db.add(new_glass)
    db.commit()

    return RedirectResponse(url=f"/invoices/{invoice_id}/glasses", status_code=303)


# ============================================================
# 3. UPDATE GLASS (form submit → redirect)
# ============================================================
@router.post("/glasses/{glass_id}/update")
def update_invoice_glass(
    glass_id: int,
    request: Request,
    purchase_order_number: Optional[str] = Form(None),
    purchase_date: Optional[str] = Form(None),
    vendor: Optional[str] = Form(None),
    vendor_invoice_number: Optional[str] = Form(None),
    vendor_invoice_date: Optional[str] = Form(None),
    nags_code: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    glass_type: Optional[str] = Form(None),
    position: Optional[str] = Form(None),
    purchase_price: Optional[str] = Form(None),
    sales_price: Optional[str] = Form(None),
    payment_status: str = Form("PENDING"),
    is_ordered: Optional[str] = Form(None),
    status: str = Form("ORDERED"),
    storage_location: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    glass = db.query(InvoiceGlass).filter(InvoiceGlass.id == glass_id).first()
    if not glass:
        raise HTTPException(status_code=404, detail="Glass not found")

    def parse_date(s):
        if not s:
            return None
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except ValueError:
            return None

    def parse_decimal(s):
        if s is None or s == "":
            return None
        try:
            return float(s)
        except ValueError:
            return None

    glass.purchase_order_number = purchase_order_number or None
    glass.purchase_date = parse_date(purchase_date)
    glass.vendor = vendor or None
    glass.vendor_invoice_number = vendor_invoice_number or None
    glass.vendor_invoice_date = parse_date(vendor_invoice_date)
    glass.nags_code = nags_code or None
    glass.description = description or None
    glass.glass_type = glass_type or None
    glass.position = position or None
    glass.purchase_price = parse_decimal(purchase_price)
    glass.sales_price = parse_decimal(sales_price)
    glass.payment_status = payment_status or "PENDING"
    glass.is_ordered = (str(is_ordered).lower() in ("on", "true", "1"))
    glass.status = status or "ORDERED"
    glass.storage_location = storage_location or None
    glass.notes = notes or None

    db.commit()

    return RedirectResponse(url=f"/invoices/{glass.invoice_id}/glasses", status_code=303)


# ============================================================
# 4. DELETE GLASS (form submit → redirect)
# ============================================================
@router.post("/glasses/{glass_id}/delete")
def delete_invoice_glass(
    glass_id: int,
    db: Session = Depends(get_db)
):
    glass = db.query(InvoiceGlass).filter(InvoiceGlass.id == glass_id).first()
    if not glass:
        raise HTTPException(status_code=404, detail="Glass not found")

    invoice_id = glass.invoice_id
    db.delete(glass)
    db.commit()

    return RedirectResponse(url=f"/invoices/{invoice_id}/glasses", status_code=303)