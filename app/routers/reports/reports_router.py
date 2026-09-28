# /app/routers/reports/reports_router.py | Updated: 2026-09-27 (company context)

from fastapi import APIRouter, Request, Query, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import date, datetime, timedelta

from app.core.template_loader import jinja as templates
from app.database.database import SessionLocal
from app.models.invoices.invoice_model import Invoice
from app.models.invoices.invoice_payment_model import InvoicePayment
from app.models.company.user import User  # noqa: F401 (registra el modelo para relationships)
from app.models.company.company import Company

router = APIRouter(prefix="/reports", tags=["Reports"])


# ============================================================
# DB DEPENDENCY
# ============================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# REPORTS MAIN MENU
# ============================================================

@router.get("")
def reports_menu(request: Request, db: Session = Depends(get_db)):
    """Reports main menu page (grid of report cards)."""
    company = db.query(Company).first()
    return templates.TemplateResponse(
        request=request,
        name="reports/reports_menu.html",
        context={
            "company": company,
        }
    )


# ============================================================
# DAILY REPORT
# ============================================================

@router.get("/daily")
def report_daily(
    request: Request,
    report_date: str = Query(default=None, alias="date"),
    db: Session = Depends(get_db)
):
    """Daily report: invoiced, collected, pending + breakdown + by technician."""

    company = db.query(Company).first()

    # --- Parse date ---
    target_date = date.today()
    if report_date:
        try:
            target_date = datetime.strptime(report_date, "%Y-%m-%d").date()
        except ValueError:
            target_date = date.today()
    report_date_str = target_date.isoformat()
    next_day = target_date + timedelta(days=1)

    # ============================================================
    # INVOICED (Facturado) — based on Invoice.created_at, exclude VOID
    # ============================================================
    invoiced_q = db.query(
        func.coalesce(func.sum(Invoice.total), 0).label("total"),
        func.coalesce(func.sum(Invoice.subtotal), 0).label("subtotal"),
        func.coalesce(func.sum(Invoice.labor_cost), 0).label("labor"),
        func.coalesce(func.sum(Invoice.materials_cost), 0).label("materials"),
        func.coalesce(func.sum(Invoice.misc_cost), 0).label("misc"),
        func.coalesce(func.sum(Invoice.tax), 0).label("tax"),
        func.count(Invoice.id).label("count"),
    ).filter(
        Invoice.created_at >= target_date,
        Invoice.created_at < next_day,
        Invoice.status != "VOID"
    ).first()

    invoiced_total      = float(invoiced_q.total or 0)
    invoiced_subtotal   = float(invoiced_q.subtotal or 0)
    invoiced_labor      = float(invoiced_q.labor or 0)
    invoiced_materials  = float(invoiced_q.materials or 0)
    invoiced_misc       = float(invoiced_q.misc or 0)
    invoiced_tax        = float(invoiced_q.tax or 0)
    invoiced_count      = int(invoiced_q.count or 0)
    mobile_fee          = invoiced_total - invoiced_subtotal - invoiced_tax

    # ============================================================
    # COLLECTED — two views
    #   1) by capture date  : InvoicePayment.created_at
    #   2) by payment_date  : user-entered date
    # Only status IN (DEPOSITED, PENDING)
    # ============================================================
    collected_capture = db.query(
        func.coalesce(func.sum(InvoicePayment.amount), 0)
    ).filter(
        InvoicePayment.created_at >= target_date,
        InvoicePayment.created_at < next_day,
        InvoicePayment.payment_status.in_(["DEPOSITED", "PENDING"])
    ).scalar() or 0

    collected_payment_date = db.query(
        func.coalesce(func.sum(InvoicePayment.amount), 0)
    ).filter(
        InvoicePayment.payment_date == target_date,
        InvoicePayment.payment_status.in_(["DEPOSITED", "PENDING"])
    ).scalar() or 0

    collected_capture      = float(collected_capture)
    collected_payment_date = float(collected_payment_date)

    # Pending = invoiced - collected (using capture date as primary)
    pending = invoiced_total - collected_capture

    # ============================================================
    # BY TECHNICIAN — invoices of the day (exclude VOID)
    # ============================================================
    invoices_day = db.query(Invoice).options(
        joinedload(Invoice.technician)
    ).filter(
        Invoice.created_at >= target_date,
        Invoice.created_at < next_day,
        Invoice.status != "VOID"
    ).order_by(Invoice.technician_id, Invoice.id).all()

    invoice_ids = [inv.id for inv in invoices_day]

    # Paid per invoice (DEPOSITED + PENDING)
    payments_map = {}
    if invoice_ids:
        payments_rows = db.query(
            InvoicePayment.invoice_id,
            func.coalesce(func.sum(InvoicePayment.amount), 0).label("paid")
        ).filter(
            InvoicePayment.invoice_id.in_(invoice_ids),
            InvoicePayment.payment_status.in_(["DEPOSITED", "PENDING"])
        ).group_by(InvoicePayment.invoice_id).all()
        payments_map = {row.invoice_id: float(row.paid or 0) for row in payments_rows}

    tech_map = {}
    for inv in invoices_day:
        tech_id   = inv.technician_id
        tech_name = inv.technician.full_name if inv.technician else "Unassigned"

        if tech_id not in tech_map:
            tech_map[tech_id] = {
                "technician_id":   tech_id,
                "technician_name": tech_name,
                "invoices":        [],
                "total_invoiced":  0.0,
                "total_paid":      0.0,
            }

        paid    = payments_map.get(inv.id, 0.0)
        total   = float(inv.total or 0)
        vehicle = f"{inv.vehicle_make or ''} {inv.vehicle_model or ''}".strip()

        tech_map[tech_id]["invoices"].append({
            "id":             inv.id,
            "invoice_number": inv.invoice_number or f"#{inv.id}",
            "customer_id":    inv.customer_id,
            "vehicle":        vehicle,
            "total":          total,
            "paid":           paid,
            "balance":        total - paid,
            "status":         inv.status or "",
        })
        tech_map[tech_id]["total_invoiced"] += total
        tech_map[tech_id]["total_paid"]     += paid

    technicians = list(tech_map.values())
    for t in technicians:
        t["total_balance"] = t["total_invoiced"] - t["total_paid"]
    technicians.sort(key=lambda t: t["total_invoiced"], reverse=True)

    # ============================================================
    # CONTEXT
    # ============================================================
    summary = {
        "invoiced_total":          invoiced_total,
        "invoiced_subtotal":       invoiced_subtotal,
        "invoiced_labor":          invoiced_labor,
        "invoiced_materials":      invoiced_materials,
        "invoiced_misc":           invoiced_misc,
        "invoiced_tax":            invoiced_tax,
        "mobile_fee":              mobile_fee,
        "invoiced_count":          invoiced_count,
        "collected_capture":       collected_capture,
        "collected_payment_date":  collected_payment_date,
        "pending":                 pending,
    }

    return templates.TemplateResponse(
        request=request,
        name="reports/report_daily.html",
        context={
            "company":     company,
            "report_date": report_date_str,
            "summary":     summary,
            "technicians": technicians,
        }
    )