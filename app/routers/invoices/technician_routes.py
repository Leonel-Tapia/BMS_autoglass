# RUTA: app/routers/invoices/technician_routes.py
# CREADO: 2026-09-04
# ACTUALIZADO: 2026-09-25 - Agregado Customer.email al query (para botón Email)

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime
from typing import Optional
from io import BytesIO
from xhtml2pdf import pisa
from app.database.database import get_db
from app.models.invoices.invoice_model import Invoice, InvoiceItem
from app.models.invoices.invoice_payment_model import InvoicePayment
from app.models.invoices.invoice_glass_model import InvoiceGlass
from app.models.customers.customer_model import Customer
from app.models.company.company import Company
from app.core.template_loader import jinja as templates

router = APIRouter(prefix="/technician", tags=["Technician"])

# Orden fijo para mostrar métodos de pago
PAYMENT_METHODS_ORDER = [
    "CASH",
    "CREDIT_CARD",
    "DEBIT_CARD",
    "CHECK",
    "TRANSFER",
    "ZELLE",
    "OTHER",
]

# Etiquetas legibles
PAYMENT_METHOD_LABELS = {
    "CASH": "Cash",
    "CREDIT_CARD": "Credit Card",
    "DEBIT_CARD": "Debit Card",
    "CHECK": "Check",
    "TRANSFER": "Transfer",
    "ZELLE": "Zelle",
    "OTHER": "Other",
}


def _get_daily_closing_data(db: Session, user_id: int, target_date: date, service_type_clean: str):
    """
    Función auxiliar: arma los datos del Daily Closing para no duplicar lógica
    entre el HTML y el PDF.
    """
    query = (
        db.query(
            InvoicePayment.id,
            InvoicePayment.invoice_id,
            InvoicePayment.payment_type,
            InvoicePayment.amount,
            InvoicePayment.reference,
            InvoicePayment.payment_date,
            InvoicePayment.payment_status,
            InvoicePayment.created_by,
            Customer.name.label("customer_name"),
        )
        .join(Invoice, InvoicePayment.invoice_id == Invoice.id)
        .join(Customer, Invoice.customer_id == Customer.id)
        .filter(InvoicePayment.payment_date == target_date)
        .filter(Invoice.technician_id == user_id)
        .filter(InvoicePayment.payment_status.in_(["DEPOSITED", "PENDING"]))
    )

    if service_type_clean == "SHOP":
        query = query.filter(Invoice.service_type == "SHOP")
    else:
        query = query.filter(Invoice.service_type.in_(["MOVIL", "MOBILE", "Mobile", "mobile", "Movil"]))

    payments = query.order_by(InvoicePayment.id.asc()).all()

    totals_by_method = {m: 0.0 for m in PAYMENT_METHODS_ORDER}
    for p in payments:
        method = (p.payment_type or "OTHER").strip().upper()
        if method not in totals_by_method:
            totals_by_method[method] = 0.0
        totals_by_method[method] += float(p.amount or 0)

    grand_total = sum(totals_by_method.values())

    return payments, totals_by_method, grand_total


# ============================================================
# DASHBOARD (con fecha seleccionable)
# ============================================================
@router.get("/dashboard", response_class=HTMLResponse)
def technician_dashboard(
    request: Request,
    selected_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Verificar que el usuario esté autenticado y sea técnico
    user_id = request.session.get("user_id")
    user_role = request.session.get("role")

    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=303)

    if user_role != "technician":
        return RedirectResponse(url="/company/main_menu", status_code=303)

    # Fecha seleccionable (default = hoy)
    if selected_date:
        try:
            target_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
        except ValueError:
            target_date = date.today()
    else:
        target_date = date.today()

    # Filtrado por estimated_appointment_date
    # Incluye customer_phone + customer_email + city/state/zip + status (para el badge)
    invoices = (
        db.query(
            Invoice.id,
            Invoice.estimated_appointment_time,
            Invoice.service_type,
            Customer.name.label("customer_name"),
            Customer.phone.label("customer_phone"),
            Customer.email.label("customer_email"),
            Customer.address.label("customer_address"),
            Customer.city.label("customer_city"),
            Customer.state.label("customer_state"),
            Customer.zip_code.label("customer_zip"),
            Invoice.vehicle_make,
            Invoice.vehicle_model,
            Invoice.total,
            Invoice.status,
            Invoice.payment_status,
            Invoice.payment_amount1,
            Invoice.payment_amount2,
            (Invoice.total - func.coalesce(Invoice.payment_amount1, 0) - func.coalesce(Invoice.payment_amount2, 0)).label("balance")
        )
        .join(Customer, Invoice.customer_id == Customer.id)
        .filter(Invoice.technician_id == user_id)
        .filter(Invoice.estimated_appointment_date == target_date)
        .order_by(Invoice.estimated_appointment_time.asc())
        .all()
    )

    # glass_info: dict con los items (NAGS) por invoice
    # Estructura: { invoice_id: [ {"nags": "...", "description": "...", "quantity": 1}, ... ] }
    glass_info = {}
    invoice_ids = []
    if invoices:
        invoice_ids = [inv.id for inv in invoices]
        all_items = db.query(InvoiceItem).filter(InvoiceItem.invoice_id.in_(invoice_ids)).all()
        for item in all_items:
            if item.invoice_id not in glass_info:
                glass_info[item.invoice_id] = []
            glass_info[item.invoice_id].append({
                "nags": item.product_name or "",
                "description": item.description or "",
                "quantity": item.quantity or 1,
            })

    # glass_pickup_list: vidrios ORDERED de los invoices del día
    glass_pickup_list = []
    if invoice_ids:
        glasses = (
            db.query(InvoiceGlass)
            .filter(InvoiceGlass.invoice_id.in_(invoice_ids))
            .filter(InvoiceGlass.status == "ORDERED")
            .order_by(InvoiceGlass.invoice_id.asc(), InvoiceGlass.id.asc())
            .all()
        )
        inv_map = {inv.id: inv for inv in invoices}
        for g in glasses:
            inv = inv_map.get(g.invoice_id)
            glass_pickup_list.append({
                "id": g.id,
                "invoice_id": g.invoice_id,
                "nags_code": g.nags_code or "",
                "description": g.description or "",
                "glass_type": g.glass_type or "",
                "position": g.position or "",
                "vendor": g.vendor or "",
                "customer_name": inv.customer_name if inv else "",
            })

    # Obtener el nombre del técnico
    technician_name = request.session.get("user_name", "Técnico")

    return templates.TemplateResponse(
        request=request,
        name="invoices/technician_dashboard.html",
        context={
            "technician_name": technician_name,
            "invoices": invoices,
            "glass_info": glass_info,
            "glass_pickup_list": glass_pickup_list,
            "today": date.today(),
            "target_date": target_date,
            "selected_date": target_date.strftime("%Y-%m-%d"),
        }
    )


# ============================================================
# MARCAR VIDRIO COMO RECIBIDO
# ============================================================
@router.post("/glass/{glass_id}/received", response_class=JSONResponse)
def mark_glass_received(
    glass_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    El técnico marca un vidrio como RECEIVED.
    Guarda received_at + received_by.
    """
    user_id = request.session.get("user_id")
    user_role = request.session.get("role")

    if not user_id or user_role != "technician":
        return JSONResponse({"success": False, "error": "Unauthorized"}, status_code=401)

    glass = db.query(InvoiceGlass).filter(InvoiceGlass.id == glass_id).first()
    if not glass:
        return JSONResponse({"success": False, "error": "Glass not found"}, status_code=404)

    if glass.status != "ORDERED":
        return JSONResponse({"success": False, "error": f"Glass already marked as {glass.status}"}, status_code=400)

    technician_name = request.session.get("user_name") or request.session.get("username") or "Technician"

    glass.status = "RECEIVED"
    glass.received_at = datetime.now()
    glass.received_by = technician_name

    db.commit()

    return JSONResponse({
        "success": True,
        "message": f"✓ {glass.nags_code or 'Glass'} marked as Received",
        "glass_id": glass.id,
        "received_at": glass.received_at.isoformat() if glass.received_at else None,
        "received_by": glass.received_by,
    })


# ============================================================
# DAILY CLOSING REPORT (para técnico)
# ============================================================
@router.get("/daily-closing", response_class=HTMLResponse)
def technician_daily_closing(
    request: Request,
    selected_date: Optional[str] = None,
    service_type: Optional[str] = "MOVIL",
    db: Session = Depends(get_db)
):
    """
    Reporte de cierre diario para el técnico logueado.
    Filtra por fecha de PAGO (payment_date) y por tipo de servicio (MOVIL / SHOP).
    Muestra únicamente pagos con status DEPOSITED o PENDING.
    """
    # 1. Validar sesión
    user_id = request.session.get("user_id")
    user_role = request.session.get("role")

    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=303)

    if user_role != "technician":
        return RedirectResponse(url="/company/main_menu", status_code=303)

    # 2. Parsear fecha (default = hoy)
    if selected_date:
        try:
            target_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
        except ValueError:
            target_date = date.today()
    else:
        target_date = date.today()

    # 3. Normalizar tipo de servicio
    service_type_clean = (service_type or "MOVIL").strip().upper()

    # 4. Obtener datos
    payments, totals_by_method, grand_total = _get_daily_closing_data(
        db, user_id, target_date, service_type_clean
    )

    # 5. Nombre del técnico
    technician_name = request.session.get("user_name", "Technician")

    return templates.TemplateResponse(
        request=request,
        name="invoices/technician_daily_closing.html",
        context={
            "technician_name": technician_name,
            "selected_date": target_date.strftime("%Y-%m-%d"),
            "target_date": target_date,
            "service_type": "SHOP" if service_type_clean == "SHOP" else "MOVIL",
            "payments": payments,
            "totals_by_method": totals_by_method,
            "grand_total": grand_total,
            "method_labels": PAYMENT_METHOD_LABELS,
            "method_order": PAYMENT_METHODS_ORDER,
            "today": date.today(),
        }
    )


# ============================================================
# DAILY CLOSING PDF (descarga directa)
# ============================================================
@router.get("/daily-closing/download")
def technician_daily_closing_pdf(
    request: Request,
    selected_date: Optional[str] = None,
    service_type: Optional[str] = "MOVIL",
    db: Session = Depends(get_db)
):
    """
    Genera el PDF del Daily Closing y lo devuelve como descarga.
    Mismos filtros que la vista HTML.
    """
    # 1. Validar sesión
    user_id = request.session.get("user_id")
    user_role = request.session.get("role")

    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=303)

    if user_role != "technician":
        return RedirectResponse(url="/company/main_menu", status_code=303)

    # 2. Parsear fecha
    if selected_date:
        try:
            target_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
        except ValueError:
            target_date = date.today()
    else:
        target_date = date.today()

    # 3. Normalizar tipo de servicio
    service_type_clean = (service_type or "MOVIL").strip().upper()

    # 4. Obtener datos
    payments, totals_by_method, grand_total = _get_daily_closing_data(
        db, user_id, target_date, service_type_clean
    )

    technician_name = request.session.get("user_name", "Technician")

    # 5. Renderizar el template de PDF
    html = templates.get_template("invoices/technician_daily_closing_pdf.html").render(
        {
            "technician_name": technician_name,
            "target_date": target_date,
            "service_type": "SHOP" if service_type_clean == "SHOP" else "MOVIL",
            "payments": payments,
            "totals_by_method": totals_by_method,
            "grand_total": grand_total,
            "method_labels": PAYMENT_METHOD_LABELS,
            "method_order": PAYMENT_METHODS_ORDER,
            "now": datetime.now(),
        }
    )

    # 6. Generar PDF en memoria
    pdf_buffer = BytesIO()
    pisa.CreatePDF(BytesIO(html.encode("utf-8")), pdf_buffer)
    pdf_buffer.seek(0)

    # 7. Nombre del archivo
    filename = f"daily_closing_{target_date.strftime('%Y-%m-%d')}_{service_type_clean}.pdf"

    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )