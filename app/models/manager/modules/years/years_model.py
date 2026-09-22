# /app/models/manager/modules/years/years_model.py – actualizado 2026-06-26 18:51 MDT

from sqlalchemy import Column, Integer
from app.database.database import Base


class Years(Base):
    __tablename__ = "vehicle_years"


    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, unique=True, nullable=False)
