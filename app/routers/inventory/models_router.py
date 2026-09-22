# RUTA: app/routers/inventory/models_router.py | ACTUALIZADO: 2026-07-04 15:48 MDT
# DESCRIPCIÓN: Router para obtener modelos de vehículos

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.inventory.vehicle_model_model import VehicleModel

router = APIRouter(prefix="/inventory", tags=["inventory"])

@router.get("/models/{make_id}")
def get_models(make_id: int, db: Session = Depends(get_db)):
    # Filtramos modelos por el ID de la marca
    models = db.query(VehicleModel).filter(VehicleModel.make_id == make_id).all()
    return [{"id": m.id, "name": m.model} for m in models]