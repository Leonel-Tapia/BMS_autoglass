from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.database import get_db
from app.models.inventory.windshield_catalog_model import WindshieldCatalog
from app.models.purchases.purchase_model import PurchaseOrderDetail
from app.models.invoices.invoice_model import InvoiceItem

router = APIRouter(prefix="/inventory", tags=["inventory"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/stock-report", response_class=HTMLResponse)
def stock_report(request: Request, db: Session = Depends(get_db)):

    # Subconsultas para entradas (Compras) y salidas (Facturas)
    entradas_subq = db.query(
        PurchaseOrderDetail.part_number,
        func.sum(PurchaseOrderDetail.quantity_ordered).label('total_in')
    ).group_by(PurchaseOrderDetail.part_number).subquery()

    salidas_subq = db.query(
        InvoiceItem.part_number,
        func.sum(InvoiceItem.quantity).label('total_out')
    ).group_by(InvoiceItem.part_number).subquery()

    # Consulta principal cruzando WindshieldCatalog con movimientos
    query = db.query(
        WindshieldCatalog,
        func.coalesce(entradas_subq.c.total_in, 0).label('total_in'),
        func.coalesce(salidas_subq.c.total_out, 0).label('total_out')
    ).outerjoin(
        entradas_subq, WindshieldCatalog.nags_code == entradas_subq.c.part_number
    ).outerjoin(
        salidas_subq, WindshieldCatalog.nags_code == salidas_subq.c.part_number
    ).order_by(WindshieldCatalog.nags_code.asc())

    total_inventory_value = 0
    rows = []
    
    for catalog_item, total_in, total_out in query.all():
        total_in = float(total_in)
        total_out = float(total_out)
        qty = total_in - total_out

        # Misma l?gica de filtro: Mostrar si hay stock o si hubo movimientos
        if qty > 0 or total_in > 0 or total_out > 0:
            cost = float(catalog_item.cost) if catalog_item.cost else 0.00
            
            # Solo sumamos al valor total si el stock es positivo
            total_cost = qty * cost if qty > 0 else 0.00 

            total_inventory_value += total_cost

            rows.append({
                "sku": catalog_item.nags_code,
                "part_number": catalog_item.nags_code,
                "part_name": catalog_item.description,
                "qty": qty,
                "unit_cost": cost,
                "total_cost": total_cost,
                "location": ""  # Listo para usar en el futuro
            })

    return templates.TemplateResponse(
        request=request,
        name="inventory/inventory_stock_report.html",
        context={
            "rows": rows,
            "total_inventory_value": total_inventory_value
        }
    )
