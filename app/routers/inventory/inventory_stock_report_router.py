from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.database import get_db
from app.models.inventory.inventory import InventoryPart

router = APIRouter(prefix="/inventory", tags=["inventory"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/stock-report", response_class=HTMLResponse)
def stock_report(request: Request, db: Session = Depends(get_db)):

    parts = (
        db.query(InventoryPart)
        .order_by(InventoryPart.part_number.asc())
        .all()
    )

    total_inventory_value = 0

    rows = []
    for p in parts:
        qty = float(p.quantity_on_hand or 0)
        cost = float(p.unit_cost or 0)
        total_cost = qty * cost

        total_inventory_value += total_cost

        rows.append({
            "sku": p.sku,
            "part_number": p.part_number,
            "part_name": p.part_name,
            "qty": qty,
            "unit_cost": cost,
            "total_cost": total_cost,
            "location": p.location
        })

    return templates.TemplateResponse(
        request=request,
        name="inventory/inventory_stock_report.html",
        context={
            "rows": rows,
            "total_inventory_value": total_inventory_value
        }
    )
