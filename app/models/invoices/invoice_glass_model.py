# /app/models/invoices/invoice_glass_model.py
# ACTUALIZADO: 2026-09-18 - Agregado received_at + received_by (recepción por técnico)
from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, Date, TIMESTAMP, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base

class InvoiceGlass(Base):
    __tablename__ = "invoice_glasses"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)

    # Información de compra
    purchase_order_number = Column(String(50), nullable=True)
    purchase_date = Column(Date, nullable=True)

    # Proveedor (wholesaler)
    vendor = Column(String(100), nullable=True)                 # Mygrant, Pilkington, etc.
    vendor_invoice_number = Column(String(50), nullable=True)
    vendor_invoice_date = Column(Date, nullable=True)

    # Identificación del vidrio
    nags_code = Column(String(50), nullable=True)
    description = Column(String(255), nullable=True)
    glass_type = Column(String(50), nullable=True)
    position = Column(String(50), nullable=True)

    # Precios
    purchase_price = Column(DECIMAL(10, 2), nullable=True)
    sales_price = Column(DECIMAL(10, 2), nullable=True)

    # Estados
    # payment_status: PAID / CREDIT / PENDING
    payment_status = Column(String(20), default="PENDING", nullable=False)

    # is_ordered: si ya se ordenó al wholesaler
    is_ordered = Column(Boolean, default=False, nullable=False)

    # status: ORDERED / RECEIVED / INSTALLED / DAMAGED / RETURNED / CANCELLED
    status = Column(String(20), default="ORDERED", nullable=False, index=True)

    # Almacenamiento
    storage_location = Column(String(100), nullable=True)

    # Devoluciones
    return_date = Column(Date, nullable=True)
    return_reason = Column(String(255), nullable=True)

    # NUEVO 2026-09-18: Recepción por parte del técnico
    received_at = Column(TIMESTAMP, nullable=True)
    received_by = Column(String(100), nullable=True)

    # Notas
    notes = Column(Text, nullable=True)

    # Auditoría
    created_by = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relación con Invoice
    invoice = relationship("Invoice", backref="glasses")

    def __repr__(self):
        return f"<InvoiceGlass(id={self.id}, invoice_id={self.invoice_id}, status={self.status}, vendor={self.vendor})>"

    def to_dict(self):
        """Convierte el modelo a diccionario para respuestas JSON"""
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "purchase_order_number": self.purchase_order_number,
            "purchase_date": self.purchase_date.isoformat() if self.purchase_date else None,
            "vendor": self.vendor,
            "vendor_invoice_number": self.vendor_invoice_number,
            "vendor_invoice_date": self.vendor_invoice_date.isoformat() if self.vendor_invoice_date else None,
            "nags_code": self.nags_code,
            "description": self.description,
            "glass_type": self.glass_type,
            "position": self.position,
            "purchase_price": float(self.purchase_price) if self.purchase_price else 0.00,
            "sales_price": float(self.sales_price) if self.sales_price else 0.00,
            "payment_status": self.payment_status,
            "is_ordered": self.is_ordered,
            "status": self.status,
            "storage_location": self.storage_location,
            "return_date": self.return_date.isoformat() if self.return_date else None,
            "return_reason": self.return_reason,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "received_by": self.received_by,
            "notes": self.notes,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    # ===== Helpers de estado =====

    def mark_received(self, storage_location: str = None, received_by: str = None):
        """Marcar vidrio como recibido por el técnico"""
        from datetime import datetime
        self.status = "RECEIVED"
        self.received_at = datetime.now()
        if received_by:
            self.received_by = received_by
        if storage_location:
            self.storage_location = storage_location

    def mark_installed(self):
        """Marcar vidrio como instalado en vehículo"""
        self.status = "INSTALLED"

    def mark_damaged(self, reason: str = None):
        """Marcar vidrio como dañado (se debe crear otra fila nueva)"""
        self.status = "DAMAGED"
        if reason:
            self.notes = (self.notes + "\n" if self.notes else "") + f"DAMAGED: {reason}"

    def mark_returned(self, return_date, reason: str = None):
        """Marcar vidrio como devuelto al wholesaler"""
        self.status = "RETURNED"
        self.return_date = return_date
        if reason:
            self.return_reason = reason

    def mark_cancelled(self, reason: str = None):
        """Cancelar la compra del vidrio"""
        self.status = "CANCELLED"
        if reason:
            self.notes = (self.notes + "\n" if self.notes else "") + f"CANCELLED: {reason}"