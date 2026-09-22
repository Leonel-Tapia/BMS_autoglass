# RUTA: app/models/purchases/purchase_model.py
# ACTUALIZADO: 2026-05-20 09:50
# DESCRIPCIÓN: Modelos de SQLAlchemy para Órdenes de Compra

from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey, Text, DateTime, FetchedValue
from sqlalchemy.orm import relationship
from datetime import date, datetime

from app.database.database import Base 

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    po_number = Column(String(30), unique=True, index=True, nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="RESTRICT"), nullable=False)
    
    po_date = Column(Date, default=date.today, nullable=False)
    expected_delivery_date = Column(Date, nullable=True)
    actual_delivery_date = Column(Date, nullable=True)
    
    payment_terms = Column(Integer, nullable=True)
    payment_type = Column(String(30), nullable=True)
    vendor_invoice_number = Column(String(50), nullable=True)
    
    shipping_handling = Column(Numeric(12, 2), default=0.00, nullable=True)
    tax_amount = Column(Numeric(12, 2), default=0.00, nullable=True)
    subtotal = Column(Numeric(12, 2), default=0.00, nullable=True)
    grand_total = Column(Numeric(12, 2), default=0.00, nullable=True)
    
    internal_notes = Column(Text, nullable=True)
    status = Column(String(20), default="Draft", nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    vendor = relationship("Vendor", backref="purchase_orders")
    details = relationship("PurchaseOrderDetail", back_populates="purchase_order", cascade="all, delete-orphan")


class PurchaseOrderDetail(Base):
    __tablename__ = "purchase_order_details"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    
    part_number = Column(String(50), nullable=False)
    item_description = Column(String(255), nullable=False)
    
    quantity_ordered = Column(Numeric(12, 2), default=0.00, nullable=False)   
    unit_cost = Column(Numeric(12, 4), default=0.0000, nullable=False)
    line_subtotal = Column(Numeric(12, 2), default=0.00, nullable=False)
    
    received_qty = Column(Numeric(12, 2), default=0.00, nullable=True)
    
    # Columna calculada en base de datos, no enviar en el INSERT
    pending_qty = Column(Numeric(12, 2), server_default=FetchedValue(), nullable=True)

    purchase_order = relationship("PurchaseOrder", back_populates="details")