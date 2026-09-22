# RUTA: app/models/inventory/windshield_catalog_model.py
# ACTUALIZADO: 2026-07-06 17:45 MDT
# Modelo alineado EXACTAMENTE con la tabla real windshield_catalog

from sqlalchemy import Column, Integer, String, Text, Numeric
from app.database.database import Base

class WindshieldCatalog(Base):
    __tablename__ = "windshield_catalog"

    id = Column(Integer, primary_key=True, index=True)
    nags_code = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)

    year_from = Column(Integer, nullable=True)
    year_to = Column(Integer, nullable=True)

    make_id = Column(Integer, nullable=True)
    model_id = Column(Integer, nullable=True)
    trim_id = Column(Integer, nullable=True)

    features = Column(Text, nullable=True)

    cost = Column(Numeric, nullable=True)
    price = Column(Numeric, nullable=True)
