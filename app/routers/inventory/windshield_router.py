# RUTA: app/routers/inventory/windshield_router.py | ACTUALIZADO: 2026-07-21
# DESCRIPCIÓN: Router para la gestión y catálogo de parabrisas

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.inventory.windshield_catalog_model import WindshieldCatalog

router = APIRouter(prefix="/inventory", tags=["windshield"])
templates = Jinja2Templates(directory="app/templates")

# 1. Endpoint original en JSON (Usado por los estimados)
@router.get("/windshield")
def get_windshield_catalog(db: Session = Depends(get_db)):
    """
    Devuelve el catálogo de parabrisas en formato JSON para el datalist del Estimate.
    """
    items = db.query(WindshieldCatalog).all()

    return [
        {
            "nags_code": item.nags_code,
            "description": item.description,
            "cost": float(item.cost) if item.cost is not None else 0.00,
            "price": float(item.price) if item.price is not None else 0.00
        }
        for item in items
    ]


# 2. NUEVO: Vista HTML para la administración del Catálogo en Manager (Ruta corregida según la estructura de subcarpetas)
@router.get("/windshield/manage")
def manage_windshield_catalog(request: Request, db: Session = Depends(get_db)):
    items = db.query(WindshieldCatalog).order_by(WindshieldCatalog.nags_code.asc()).all()
    return templates.TemplateResponse(
        request,
        "manager/modules/windshields/windshield_catalog_list.html",
        {"items": items}
    )


# 3. NUEVO: Procesar formulario para agregar un nuevo parabrisas
@router.post("/windshield/add")
def add_windshield_item(
    nags_code: str = Form(...),
    description: str = Form(...),
    cost: float = Form(...),
    price: float = Form(...),
    db: Session = Depends(get_db)
):
    code_clean = nags_code.strip().upper()
    if code_clean:
        exists = db.query(WindshieldCatalog).filter(WindshieldCatalog.nags_code == code_clean).first()
        if not exists:
            new_item = WindshieldCatalog(
                nags_code=code_clean,
                description=description.strip(),
                cost=cost,
                price=price
            )
            db.add(new_item)
            db.commit()

    return RedirectResponse(url="/inventory/windshield/manage", status_code=303)