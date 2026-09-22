# ============================================================
# Purchase Order Receiving Model
# BMS AUTOGLASS - Clean Architecture / No Includes / No Inheritance
# ============================================================

from sqlalchemy import Column, Integer, Numeric, String, Text, Boolean, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.database import Base   # ← IMPORT CORRECTO

class PurchaseOrderReceiving(Base):
    __tablename__ = "purchase_order_receiving"

    id = Column(Integer, primary_key=True, index=True)

    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    purchase_order_detail_id = Column(Integer, ForeignKey("purchase_order_details.id"), nullable=False)

    received_qty = Column(Numeric(12, 2), nullable=False, default=0)

    received_at = Column(TIMESTAMP, nullable=True, server_default=func.now())

    condition = Column(String(20), nullable=False, default="OK")
    notes = Column(Text, nullable=True)

    created_at = Column(TIMESTAMP, nullable=True, server_default=func.now())

    # Auditoría
    received_by = Column(String(100), nullable=False, default="system")
    created_by = Column(String(100), nullable=False, default="system")
    updated_at = Column(TIMESTAMP, nullable=True)
    updated_by = Column(String(100), nullable=True)
    is_void = Column(Boolean, nullable=False, default=False)
    void_reason = Column(String(255), nullable=True)

    # Relaciones limpias
    purchase_order = relationship("PurchaseOrder")
    purchase_order_detail = relationship("PurchaseOrderDetail")
