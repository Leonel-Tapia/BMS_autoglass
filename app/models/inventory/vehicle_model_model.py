# RUTA: app/models/inventory/vehicle_model_model.py | ACTUALIZADO: 2026-07-04 15:45 MDT
# DESCRIPCIÓN: Modelo para los modelos de vehículos vinculados a una marca

from sqlalchemy import Column, Integer, String, ForeignKey
from app.database.database import Base

class VehicleModel(Base):
    __tablename__ = "vehicle_models"
    
    id = Column(Integer, primary_key=True, index=True)
    model = Column(String, index=True)
    make_id = Column(Integer, ForeignKey("vehicle_makes.id")) # Relación con la marca