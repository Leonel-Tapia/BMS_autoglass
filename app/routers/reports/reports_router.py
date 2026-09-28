# /app/routers/reports/reports_router.py | Updated: 2026-09-27 (period report + helpers)

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

MAX_RANGE_DAYS = 731  # ~2 years


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
# HELPERS (shared by daily & period)
# ============================================================

def _invoiced_summary(db: Session, start_date: date, end_exclusive: date) -> dict:
    """Aggregate invoiced totals in [start_date, end_exclusive). Excludes VOID."""
    q = db.query(
        func.coalesce(func.sum(Invoice.total), 0).label("total"),
        func.coalesce(func.sum(Invoice.subtotal), 0).label("subtotal"),
        func.coalesce(func.sum(Invoice.labor_cost), 0).label("labor"),
        func.coalesce(func.sum(Invoice.materials_cost), 0).label("materials"),
        func.coalesce(func.sum(Invoice.misc_cost), 0).label("misc"),
        func.coalesce(func.sum(Invoice.tax), 0).label("tax"),
        func.count(Invoice.id).label("count"),
    ).filter(
        Invoice.created_at >= start_date,
        Invoice.created_at < end_exclusive,
        Invoice.status != "VOID"
    ).first()

    total     = float(q.total or 0)
    subtotal  = float(q.subtotal or 0)
    tax       = float(q.tax or 0)

    return {
        "invoiced_total":     total,
        "invoiced_subtotal":  subtotal,
        "invoiced_labor":     float(q.labor or 0),
        "invoiced_materials": float(q.materials or 0),
        "invoiced_misc":      float(q.misc or 0),
        "invoiced_tax":       tax,
        "mobile_fee":         total - subtotal - tax,
        "invoiced_count":     int(q.count or 0),
    }


def _collected_summary(db: Session, start_date: date, end_exclusive: date):
    """Return (collected_by_capture, collected_by_payment_date). DEPOSITED+PENDING only."""
    cap = db.query(
        func.coalesce(func.sum(InvoicePayment.amount), 0)
    ).filter(
        InvoicePayment.created_at >= start_date,
        InvoicePayment.created_at < end_exclusive,
        InvoicePayment.payment_status.in_(["DEPOSITED", "PENDING"])
    ).scalar() or 0

    pd = db.query(
        func.coalesce(func.sum(InvoicePayment.amount), 0)
    ).filter(
        InvoicePayment.payment_date >= start_date,
        InvoicePayment.payment_date < end_exclusive,
        InvoicePayment.payment_status.in_(["DEPOSITED", "PENDING"])
    ).scalar() or 0

    return float(cap), float(pd)


def _technicians_breakdown(db: Session, start_date: date, end_exclusive: date) -> list:
    """Return list of technicians with their invoices in the range (excludes VOID)."""
    invoices = db.query(Invoice).options(
        joinedload(Invoice.technician)
    ).filter(
        Invoice.created_at >= start_date,
        Invoice.created_at < end_exclusive,
        Invoice.status != "VOID"
    ).order_by(Invoice.technician_id, Invoice.id).all()

    invoice_ids = [inv.id for inv in invoices]

    payments_map = {}
    if invoice_ids:
        rows = db.query(
            InvoicePayment.invoice_id,
            func.coalesce(func.sum(InvoicePayment.amount), 0).label("paid")
        ).filter(
            InvoicePayment.invoice_id.in_(invoice_ids),
            InvoicePayment.payment_status.in_(["DEPOSITED", "PENDING"])
        ).group_by(InvoicePayment.invoice_id).all()
        payments_map = {r.invoice_id: float(r.paid or 0) for r in rows}

    tech_map = {}
    for inv in invoices:
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
    return technicians


# ============================================================
# DATE HELPERS
# ============================================================

def _month_range(today: date):
    """Return (first_day, last_day) of the month containing `today`."""
    first = today.replace(day=1)
    if today.month == 12:
        last = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    return first, last


def _week_range(today: date):
    """Return (monday, sunday) of the week containing `today` (week starts Monday)."""
    monday = today - timedelta(days=today.weekday())
    return monday, monday + timedelta(days=6)


def _fmt_date(d: date) -> str:
    return d.strftime("%b %d, %Y")


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
        context={"company": company}
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

    target_date = date.today()
    if report_date:
        try:
            target_date = datetime.strptime(report_date, "%Y-%m-%d").date()
        except ValueError:
            target_date = date.today()
    report_date_str = target_date.isoformat()
    next_day = target_date + timedelta(days=1)

    invoiced             = _invoiced_summary(db, target_date, next_day)
    collected_capture, collected_payment_date = _collected_summary(db, target_date, next_day)
    technicians          = _technicians_breakdown(db, target_date, next_day)

    summary = dict(invoiced)
    summary["collected_capture"]      = collected_capture
    summary["collected_payment_date"] = collected_payment_date
    summary["pending"]                = invoiced["invoiced_total"] - collected_capture

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


# ============================================================
# PERIOD REPORT
# ============================================================

@router.get("/period")
def report_period(
    request: Request,
    preset: str = Query(default=None),
    date_from: str = Query(default=None),
    date_to: str = Query(default=None),
    db: Session = Depends(get_db)
):
    """Period report: week, month, or custom range (max 2 years)."""
    company = db.query(Company).first()
    today = date.today()
    range_warning = False

    # --- Resolve date range ---
    if preset == "today":
        start, end = today, today
    elif preset == "week":
        start, end = _week_range(today)
    elif preset == "custom" and date_from and date_to:
        try:
            start = datetime.strptime(date_from, "%Y-%m-%d").date()
            end   = datetime.strptime(date_to,   "%Y-%m-%d").date()
            if start > end:
                start, end = end, start
        except ValueError:
            preset = "month"
            start, end = _month_range(today)
    else:
        preset = "month"
        start, end = _month_range(today)

    # --- Enforce max range ---
    if (end - start).days > MAX_RANGE_DAYS:
        end = start + timedelta(days=MAX_RANGE_DAYS)
        range_warning = True

    end_exclusive = end + timedelta(days=1)

    invoiced             = _invoiced_summary(db, start, end_exclusive)
    collected_capture, collected_payment_date = _collected_summary(db, start, end_exclusive)
    technicians          = _technicians_breakdown(db, start, end_exclusive)

    summary = dict(invoiced)
    summary["collected_capture"]      = collected_capture
    summary["collected_payment_date"] = collected_payment_date
    summary["pending"]                = invoiced["invoiced_total"] - collected_capture

    return templates.TemplateResponse(
        request=request,
        name="reports/report_period.html",
        context={
            "company":        company,
            "preset":         preset,
            "date_from":      start.isoformat(),
            "date_to":        end.isoformat(),
            "range_label":    f"{_fmt_date(start)} – {_fmt_date(end)}",
            "range_days":     (end - start).days + 1,
            "range_warning":  range_warning,
            "summary":        summary,
            "technicians":    technicians,
        }
    )