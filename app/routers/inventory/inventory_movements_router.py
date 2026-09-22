# Ruta: app/routers/inventory/inventory_movements_router.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse          # 👈 FALTABA ESTO
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.inventory.inventory_movement import InventoryMovement
from app.models.inventory.inventory import InventoryPart

router = APIRouter(prefix="/inventory", tags=["inventory"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/movements", response_class=HTMLResponse)
def view_movements(request: Request, db: Session = Depends(get_db)):

    movements = (
        db.query(InventoryMovement)
        .order_by(InventoryMovement.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="inventory/inventory_movements.html",
        context={"movements": movements}
    )
