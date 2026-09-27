# /app/routers/reports/reports_router.py | Updated: 2026-09-27

from fastapi import APIRouter, Request, Query
from datetime import date

from app.core.template_loader import jinja as templates

router = APIRouter(prefix="/reports", tags=["Reports"])


# ============================================================
# REPORTS MAIN MENU
# ============================================================

@router.get("")
def reports_menu(request: Request):
    """Reports main menu page (grid of report cards)."""
    return templates.TemplateResponse(
        request=request,
        name="reports/reports_menu.html",
        context={}
    )


# ============================================================
# DAILY REPORT
# ============================================================

@router.get("/daily")
def report_daily(
    request: Request,
    report_date: str = Query(default=None, alias="date")
):
    """Daily report page. If no date provided, defaults to today."""
    if not report_date:
        report_date = date.today().isoformat()

    return templates.TemplateResponse(
        request=request,
        name="reports/report_daily.html",
        context={
            "report_date": report_date,
        }
    )