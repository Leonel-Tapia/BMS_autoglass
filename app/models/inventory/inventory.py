# Ruta: app/models/inventory/inventory.py
from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, func, FetchedValue
from app.database.database import Base 

class InventoryPart(Base):
    __tablename__ = "inventory_parts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    part_number = Column(String, nullable=False)
    part_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    quantity_on_hand = Column(Integer, nullable=False, default=0)
    minimum_quantity = Column(Integer, nullable=False, default=0)
    maximum_quantity = Column(Integer, nullable=True)
    
    location = Column(String, nullable=True)
    
    unit_cost = Column(Numeric(10, 2), nullable=False, default=0.00)
    unit_sale = Column(Numeric(10, 2), nullable=False, default=0.00)
    
    # CAMBIO AQUÍ: Usamos FetchedValue() para columnas GENERATED ALWAYS
    total_cost = Column(Numeric(12, 2), FetchedValue())
    
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())