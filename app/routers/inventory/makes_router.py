# RUTA: app/routers/inventory/makes_router.py | ACTUALIZADO: 2026-07-04 15:30 MDT
# DESCRIPCIÓN: Router para la gestión de marcas de vehículos (Makes)

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.inventory.make_model import VehicleMake

router = APIRouter(prefix="/inventory", tags=["inventory"])

@router.get("/makes")
def get_makes(db: Session = Depends(get_db)):
    # Obtenemos todas las marcas de la tabla
    makes = db.query(VehicleMake).all()
    # Devolvemos la lista de nombres para el datalist
    return [{"id": m.id, "name": m.make} for m in makes]