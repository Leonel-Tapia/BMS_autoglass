# /app/routers/reports/reports_router.py | Updated: 2026-09-28 (outstanding report)

from fastapi import APIRouter, Request, Query, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import date, datetime, timedelta

from app.core.template_loader import jinja as templates
from app.database.database import SessionLocal
from app.models.invoices.invoice_model import Invoice, InvoiceItem
from app.models.invoices.invoice_payment_model import InvoicePayment
from app.models.company.user import User  # noqa: F401 (registra el modelo para relationships)
from app.models.company.company import Company
from app.models.customers.customer_model import Customer

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
# SHARED HELPERS
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


def _payments_by_invoice(db: Session, invoice_ids):
    """Return {invoice_id: paid_amount} using DEPOSITED+PENDING only."""
    if not invoice_ids:
        return {}
    rows = db.query(
        InvoicePayment.invoice_id,
        func.coalesce(func.sum(InvoicePayment.amount), 0).label("paid")
    ).filter(
        InvoicePayment.invoice_id.in_(invoice_ids),
        InvoicePayment.payment_status.in_(["DEPOSITED", "PENDING"])
    ).group_by(InvoicePayment.invoice_id).all()
    return {r.invoice_id: float(r.paid or 0) for r in rows}


def _technicians_breakdown(db: Session, start_date: date, end_exclusive: date) -> list:
    """Return list of technicians with their invoices in the range (excludes VOID)."""
    invoices = db.query(Invoice).options(
        joinedload(Invoice.technician)
    ).filter(
        Invoice.created_at >= start_date,
        Invoice.created_at < end_exclusive,
        Invoice.status != "VOID"
    ).order_by(Invoice.technician_id, Invoice.id).all()

    payments_map = _payments_by_invoice(db, [inv.id for inv in invoices])

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
    first = today.replace(day=1)
    if today.month == 12:
        last = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    return first, last


def _week_range(today: date):
    """Week starts Monday."""
    monday = today - timedelta(days=today.weekday())
    return monday, monday + timedelta(days=6)


def _fmt_date(d: date) -> str:
    return d.strftime("%b %d, %Y")


def _resolve_period(preset, date_from, date_to):
    """Return (preset, start_date, end_date, range_warning)."""
    today = date.today()
    range_warning = False

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

    if (end - start).days > MAX_RANGE_DAYS:
        end = start + timedelta(days=MAX_RANGE_DAYS)
        range_warning = True

    return preset, start, end, range_warning


# ============================================================
# REPORTS MAIN MENU
# ============================================================

@router.get("")
def reports_menu(request: Request, db: Session = Depends(get_db)):
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
    company = db.query(Company).first()
    preset, start, end, range_warning = _resolve_period(preset, date_from, date_to)
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
            "company":       company,
            "preset":        preset,
            "date_from":     start.isoformat(),
            "date_to":       end.isoformat(),
            "range_label":   f"{_fmt_date(start)} – {_fmt_date(end)}",
            "range_days":    (end - start).days + 1,
            "range_warning": range_warning,
            "summary":       summary,
            "technicians":   technicians,
        }
    )


# ============================================================
# TECHNICIAN RANKING
# ============================================================

@router.get("/technicians")
def report_technicians(
    request: Request,
    preset: str = Query(default=None),
    date_from: str = Query(default=None),
    date_to: str = Query(default=None),
    db: Session = Depends(get_db)
):
    company = db.query(Company).first()
    preset, start, end, range_warning = _resolve_period(preset, date_from, date_to)
    end_exclusive = end + timedelta(days=1)

    technicians = _technicians_breakdown(db, start, end_exclusive)

    for t in technicians:
        t["pct_collected"] = (t["total_paid"] / t["total_invoiced"] * 100) if t["total_invoiced"] > 0 else 0.0

    technicians.sort(key=lambda t: (t["technician_id"] is None, -t["total_invoiced"]))

    totals = {
        "invoiced": sum(t["total_invoiced"] for t in technicians),
        "paid":     sum(t["total_paid"] for t in technicians),
        "balance":  sum(t["total_balance"] for t in technicians),
        "count":    sum(len(t["invoices"]) for t in technicians),
    }
    totals["pct_collected"] = (totals["paid"] / totals["invoiced"] * 100) if totals["invoiced"] > 0 else 0.0

    return templates.TemplateResponse(
        request=request,
        name="reports/technicians_ranking.html",
        context={
            "company":       company,
            "preset":        preset,
            "date_from":     start.isoformat(),
            "date_to":       end.isoformat(),
            "range_label":   f"{_fmt_date(start)} – {_fmt_date(end)}",
            "range_days":    (end - start).days + 1,
            "range_warning": range_warning,
            "technicians":   technicians,
            "totals":        totals,
        }
    )


# ============================================================
# TECHNICIAN DETAIL
# ============================================================

@router.get("/technicians/{tech_id}")
def report_technician_detail(
    request: Request,
    tech_id: int,
    preset: str = Query(default=None),
    date_from: str = Query(default=None),
    date_to: str = Query(default=None),
    db: Session = Depends(get_db)
):
    company = db.query(Company).first()
    preset, start, end, range_warning = _resolve_period(preset, date_from, date_to)
    end_exclusive = end + timedelta(days=1)

    is_unassigned = (tech_id == 0)
    tech_user = None
    tech_name = "Unassigned"

    if not is_unassigned:
        tech_user = db.query(User).filter(User.id == tech_id).first()
        if tech_user:
            tech_name = tech_user.full_name
        else:
            tech_name = f"Technician #{tech_id}"

    q = db.query(Invoice).filter(
        Invoice.created_at >= start,
        Invoice.created_at < end_exclusive,
        Invoice.status != "VOID"
    )
    if is_unassigned:
        q = q.filter(Invoice.technician_id.is_(None))
    else:
        q = q.filter(Invoice.technician_id == tech_id)

    invoices = q.order_by(Invoice.id).all()
    payments_map = _payments_by_invoice(db, [inv.id for inv in invoices])

    invoice_rows = []
    total_invoiced = 0.0
    total_paid = 0.0
    labor_sum = materials_sum = misc_sum = tax_sum = subtotal_sum = 0.0

    for inv in invoices:
        paid    = payments_map.get(inv.id, 0.0)
        total   = float(inv.total or 0)
        vehicle = f"{inv.vehicle_make or ''} {inv.vehicle_model or ''}".strip()

        invoice_rows.append({
            "id":             inv.id,
            "invoice_number": inv.invoice_number or f"#{inv.id}",
            "customer_id":    inv.customer_id,
            "vehicle":        vehicle,
            "status":         inv.status or "",
            "total":          total,
            "paid":           paid,
            "balance":        total - paid,
        })

        total_invoiced += total
        total_paid     += paid
        labor_sum      += float(inv.labor_cost or 0)
        materials_sum  += float(inv.materials_cost or 0)
        misc_sum       += float(inv.misc_cost or 0)
        tax_sum        += float(inv.tax or 0)
        subtotal_sum   += float(inv.subtotal or 0)

    total_balance = total_invoiced - total_paid
    mobile_fee = total_invoiced - subtotal_sum - tax_sum
    pct_collected = (total_paid / total_invoiced * 100) if total_invoiced > 0 else 0.0

    summary = {
        "invoiced_total":     total_invoiced,
        "invoiced_labor":     labor_sum,
        "invoiced_materials": materials_sum,
        "invoiced_misc":      misc_sum,
        "invoiced_tax":       tax_sum,
        "mobile_fee":         mobile_fee,
        "collected":          total_paid,
        "balance":            total_balance,
        "pct_collected":      pct_collected,
        "invoiced_count":     len(invoices),
    }

    return templates.TemplateResponse(
        request=request,
        name="reports/technician_detail.html",
        context={
            "company":         company,
            "tech_id":         tech_id,
            "technician_name": tech_name,
            "preset":          preset,
            "date_from":       start.isoformat(),
            "date_to":         end.isoformat(),
            "range_label":     f"{_fmt_date(start)} – {_fmt_date(end)}",
            "range_days":      (end - start).days + 1,
            "range_warning":   range_warning,
            "summary":         summary,
            "invoices":        invoice_rows,
        }
    )


# ============================================================
# APPOINTMENTS REPORT
# ============================================================

_NON_COMPLETED_STATUSES = ("VOID", "CANCELLED", "NO_SHOW")


@router.get("/appointments")
def report_appointments(
    request: Request,
    preset: str = Query(default=None),
    date_from: str = Query(default=None),
    date_to: str = Query(default=None),
    db: Session = Depends(get_db)
):
    """Appointments report: scheduled vs completed vs no-show/cancelled."""
    company = db.query(Company).first()
    preset, start, end, range_warning = _resolve_period(preset, date_from, date_to)
    end_exclusive = end + timedelta(days=1)

    base_q = db.query(Invoice).filter(
        Invoice.estimated_appointment_date >= start,
        Invoice.estimated_appointment_date < end_exclusive
    )

    scheduled = base_q.count()

    completed = base_q.filter(
        ~Invoice.status.in_(_NON_COMPLETED_STATUSES)
    ).count()

    no_show   = base_q.filter(Invoice.status == "NO_SHOW").count()
    cancelled = base_q.filter(Invoice.status == "CANCELLED").count()
    voided    = base_q.filter(Invoice.status == "VOID").count()

    rate = (completed / scheduled * 100) if scheduled > 0 else 0.0

    summary = {
        "scheduled": scheduled,
        "completed": completed,
        "no_show":   no_show,
        "cancelled": cancelled,
        "voided":    voided,
        "rate":      rate,
    }

    daily_rows = []
    cursor = start
    while cursor <= end:
        day_start = cursor
        day_end   = cursor + timedelta(days=1)

        d_scheduled = db.query(func.count(Invoice.id)).filter(
            Invoice.estimated_appointment_date >= day_start,
            Invoice.estimated_appointment_date < day_end
        ).scalar() or 0

        d_completed = db.query(func.count(Invoice.id)).filter(
            Invoice.estimated_appointment_date >= day_start,
            Invoice.estimated_appointment_date < day_end,
            ~Invoice.status.in_(_NON_COMPLETED_STATUSES)
        ).scalar() or 0

        d_no_show = db.query(func.count(Invoice.id)).filter(
            Invoice.estimated_appointment_date >= day_start,
            Invoice.estimated_appointment_date < day_end,
            Invoice.status == "NO_SHOW"
        ).scalar() or 0

        d_cancelled = db.query(func.count(Invoice.id)).filter(
            Invoice.estimated_appointment_date >= day_start,
            Invoice.estimated_appointment_date < day_end,
            Invoice.status == "CANCELLED"
        ).scalar() or 0

        d_rate = (d_completed / d_scheduled * 100) if d_scheduled > 0 else 0.0

        if d_scheduled > 0:
            daily_rows.append({
                "date":       cursor.isoformat(),
                "date_label": _fmt_date(cursor),
                "scheduled":  int(d_scheduled),
                "completed":  int(d_completed),
                "no_show":    int(d_no_show),
                "cancelled":  int(d_cancelled),
                "rate":       d_rate,
            })

        cursor += timedelta(days=1)

    return templates.TemplateResponse(
        request=request,
        name="reports/report_appointments.html",
        context={
            "company":       company,
            "preset":        preset,
            "date_from":     start.isoformat(),
            "date_to":       end.isoformat(),
            "range_label":   f"{_fmt_date(start)} – {_fmt_date(end)}",
            "range_days":    (end - start).days + 1,
            "range_warning": range_warning,
            "summary":       summary,
            "daily_rows":    daily_rows,
        }
    )


# ============================================================
# TOP 200 GLASSES
# ============================================================

@router.get("/top-products")
def report_top_products(
    request: Request,
    preset: str = Query(default=None),
    date_from: str = Query(default=None),
    date_to: str = Query(default=None),
    db: Session = Depends(get_db)
):
    """Top 200 products by installed quantity (excludes VOID invoices)."""
    company = db.query(Company).first()
    preset, start, end, range_warning = _resolve_period(preset, date_from, date_to)
    end_exclusive = end + timedelta(days=1)

    q = db.query(
        InvoiceItem.part_number.label("part_number"),
        func.coalesce(func.sum(InvoiceItem.quantity), 0).label("total_qty"),
        func.count(func.distinct(InvoiceItem.invoice_id)).label("invoice_count"),
        func.coalesce(func.sum(InvoiceItem.price * InvoiceItem.quantity), 0).label("total_revenue"),
    ).join(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).filter(
        Invoice.created_at >= start,
        Invoice.created_at < end_exclusive,
        Invoice.status != "VOID"
    ).group_by(
        InvoiceItem.part_number
    ).order_by(
        func.sum(InvoiceItem.quantity).desc()
    ).limit(200)

    rows = []
    grand_qty = 0
    grand_revenue = 0.0
    for idx, r in enumerate(q.all(), start=1):
        qty     = int(r.total_qty or 0)
        revenue = float(r.total_revenue or 0)
        rows.append({
            "rank":          idx,
            "part_number":   r.part_number or "—",
            "total_qty":     qty,
            "invoice_count": int(r.invoice_count or 0),
            "total_revenue": revenue,
        })
        grand_qty     += qty
        grand_revenue += revenue

    summary = {
        "unique_products": len(rows),
        "total_qty":       grand_qty,
        "total_revenue":   grand_revenue,
    }

    return templates.TemplateResponse(
        request=request,
        name="reports/report_top_products.html",
        context={
            "company":       company,
            "preset":        preset,
            "date_from":     start.isoformat(),
            "date_to":       end.isoformat(),
            "range_label":   f"{_fmt_date(start)} – {_fmt_date(end)}",
            "range_days":    (end - start).days + 1,
            "range_warning": range_warning,
            "summary":       summary,
            "rows":          rows,
        }
    )


# ============================================================
# OUTSTANDING (PENDING BALANCES)
# ============================================================

@router.get("/outstanding")
def report_outstanding(
    request: Request,
    preset: str = Query(default="all"),
    date_from: str = Query(default=None),
    date_to: str = Query(default=None),
    db: Session = Depends(get_db)
):
    """Outstanding report: invoices with pending balance (all-time by default)."""
    company = db.query(Company).first()
    today = date.today()
    range_warning = False
    range_label = None
    range_days = None
    start = None
    end = None
    end_exclusive = None

    # ---- Resolve date range ----
    if preset == "custom" and date_from and date_to:
        try:
            start = datetime.strptime(date_from, "%Y-%m-%d").date()
            end   = datetime.strptime(date_to,   "%Y-%m-%d").date()
            if start > end:
                start, end = end, start
        except ValueError:
            preset = "all"
            start = end = None
    elif preset == "month":
        start, end = _month_range(today)
    elif preset == "year":
        start = today.replace(month=1, day=1)
        end   = today.replace(month=12, day=31)
    else:
        preset = "all"

    if start and end:
        if (end - start).days > MAX_RANGE_DAYS:
            end = start + timedelta(days=MAX_RANGE_DAYS)
            range_warning = True
        end_exclusive = end + timedelta(days=1)
        range_label   = f"{_fmt_date(start)} – {_fmt_date(end)}"
        range_days    = (end - start).days + 1

    # ---- Query invoices with outstanding status ----
    q = db.query(Invoice).filter(
        Invoice.status.in_(["PENDING", "PARTIALLY_PAID"])
    )
    if end_exclusive:
        q = q.filter(
            Invoice.created_at >= start,
            Invoice.created_at < end_exclusive
        )
    invoices = q.all()

    payments_map = _payments_by_invoice(db, [inv.id for inv in invoices])

    # ---- Bulk-load customer names ----
    customer_ids = list({inv.customer_id for inv in invoices if inv.customer_id})
    customers_map = {}
    if customer_ids:
        custs = db.query(Customer).filter(Customer.id.in_(customer_ids)).all()
        customers_map = {c.id: c.name for c in custs}

    # ---- Build rows ----
    rows = []
    grand_total   = 0.0
    grand_paid    = 0.0
    grand_balance = 0.0

    for inv in invoices:
        paid    = payments_map.get(inv.id, 0.0)
        total   = float(inv.total or 0)
        balance = total - paid

        if balance <= 0:
            continue  # sanity check

        inv_date = inv.created_at.date() if inv.created_at else None
        age_days = (today - inv_date).days if inv_date else 0
        vehicle  = f"{inv.vehicle_make or ''} {inv.vehicle_model or ''}".strip()

        rows.append({
            "id":             inv.id,
            "invoice_number": inv.invoice_number or f"#{inv.id}",
            "customer_id":    inv.customer_id,
            "customer_name":  customers_map.get(inv.customer_id, f"#{inv.customer_id}"),
            "vehicle":        vehicle,
            "date_iso":       inv_date.isoformat() if inv_date else "",
            "date_label":     _fmt_date(inv_date) if inv_date else "—",
            "age_days":       age_days,
            "total":          total,
            "paid":           paid,
            "balance":        balance,
            "status":         inv.status or "",
        })
        grand_total   += total
        grand_paid    += paid
        grand_balance += balance

    rows.sort(key=lambda r: r["balance"], reverse=True)

    summary = {
        "count":   len(rows),
        "total":   grand_total,
        "paid":    grand_paid,
        "balance": grand_balance,
    }

    return templates.TemplateResponse(
        request=request,
        name="reports/report_outstanding.html",
        context={
            "company":       company,
            "preset":        preset,
            "date_from":     start.isoformat() if start else "",
            "date_to":       end.isoformat() if end else "",
            "range_label":   range_label,
            "range_days":    range_days,
            "range_warning": range_warning,
            "summary":       summary,
            "rows":          rows,
        }
    )