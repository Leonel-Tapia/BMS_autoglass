# Ruta: app/models/inventory/inventory_movement.py

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.database import Base

class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    part_id = Column(Integer, ForeignKey("inventory_parts.id"), nullable=False)

    movement_type = Column(String(20), nullable=False)   # IN, OUT, ADJUST
    quantity = Column(Numeric(18, 4), nullable=False, default=0)
    unit_cost = Column(Numeric(18, 4), nullable=False, default=0)
    total_cost = Column(Numeric(18, 4), nullable=False, default=0)

    reference_type = Column(String(20), nullable=True)   # PO, INVOICE, MANUAL
    reference_id = Column(Integer, nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    created_by = Column(String(50), nullable=True, default="system")

    # Relación opcional (útil para reportes)
    part = relationship("InventoryPart")
