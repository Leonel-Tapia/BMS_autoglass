# RUTA: app/models/inventory/vehicle_trim_model.py | ACTUALIZADO: 2026-07-21
# DESCRIPCIÓN: Modelo de base de datos para los Trims de vehículos

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base

class VehicleTrim(Base):
    __tablename__ = "vehicle_trims"  # Asegúrate de que coincida con el nombre de tu tabla en la BD

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("vehicle_models.id", ondelete="CASCADE"), nullable=False)
    trim = Column(String(100), nullable=False)

    # Relación opcional inversa con VehicleModel
    vehicle_model = relationship("VehicleModel", backref="trims")