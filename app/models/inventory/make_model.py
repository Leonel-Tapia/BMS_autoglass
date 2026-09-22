# RUTA: app/models/inventory/make_model.py | ACTUALIZADO: 2026-07-04 15:40 MDT
# DESCRIPCIÓN: Modelo de datos para las marcas de vehículos

from sqlalchemy import Column, Integer, String
from app.database.database import Base

class VehicleMake(Base):
    __tablename__ = "vehicle_makes"
    
    id = Column(Integer, primary_key=True, index=True)
    make = Column(String, index=True)

    def __repr__(self):
        return f"<VehicleMake(id={self.id}, make='{self.make}')>"