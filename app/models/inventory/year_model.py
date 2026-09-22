from sqlalchemy import Column, Integer, Table
from app.database.database import Base

class Year(Base):
    __tablename__ = "vehicle_years"

    __table_args__ = {'extend_existing': True}   # ⭐ SOLUCIÓN

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False)
