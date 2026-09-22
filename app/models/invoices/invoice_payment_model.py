# /app/models/invoices/invoice_payment_model.py     08/24/26  7:50 pm
from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, Date, TIMESTAMP, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base

class InvoicePayment(Base):
    __tablename__ = "invoice_payments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Tipo de pago: CASH, CREDIT_CARD, DEBIT_CARD, CHECK, TRANSFER, ZELLE, OTHER
    payment_type = Column(String(50), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    reference = Column(String(100), nullable=True)
    payment_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Estados: PENDING, DEPOSITED, BOUNCED, CANCELLED, VOID, REJECTED, FAILED, REFUNDED
    payment_status = Column(String(50), default="PENDING", nullable=False)
    
    # Información de depósito
    deposited_at = Column(TIMESTAMP, nullable=True)
    deposited_by = Column(String(100), nullable=True)
    
    # Información de rechazo
    rejection_reason = Column(Text, nullable=True)
    rejection_date = Column(TIMESTAMP, nullable=True)
    rejected_by = Column(String(100), nullable=True)
    
    # Cargos por rechazo (NSF, bank fee, etc.)
    fee_amount = Column(DECIMAL(10, 2), default=0.00, nullable=False)
    
    # Auditoría
    created_by = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relación con Invoice
    invoice = relationship("Invoice", backref="payments")

    def __repr__(self):
        return f"<InvoicePayment(id={self.id}, invoice_id={self.invoice_id}, amount={self.amount}, status={self.payment_status})>"

    def to_dict(self):
        """Convierte el modelo a diccionario para respuestas JSON"""
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "payment_type": self.payment_type,
            "amount": float(self.amount) if self.amount else 0.00,
            "reference": self.reference,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "notes": self.notes,
            "payment_status": self.payment_status,
            "deposited_at": self.deposited_at.isoformat() if self.deposited_at else None,
            "deposited_by": self.deposited_by,
            "rejection_reason": self.rejection_reason,
            "rejection_date": self.rejection_date.isoformat() if self.rejection_date else None,
            "rejected_by": self.rejected_by,
            "fee_amount": float(self.fee_amount) if self.fee_amount else 0.00,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def deposit(self, deposited_by: str):
        """Marcar pago como depositado"""
        self.payment_status = "DEPOSITED"
        self.deposited_at = func.now()
        self.deposited_by = deposited_by

    def reject(self, rejected_by: str, reason: str, fee_amount: float = 0.00):
        """Marcar pago como rechazado"""
        self.payment_status = "REJECTED"
        self.rejection_date = func.now()
        self.rejected_by = rejected_by
        self.rejection_reason = reason
        self.fee_amount = fee_amount

    def bounce(self, rejected_by: str, reason: str, fee_amount: float = 0.00):
        """Marcar pago como devuelto (bounced)"""
        self.payment_status = "BOUNCED"
        self.rejection_date = func.now()
        self.rejected_by = rejected_by
        self.rejection_reason = reason
        self.fee_amount = fee_amount

    def cancel(self):
        """Cancelar pago"""
        self.payment_status = "CANCELLED"

    def void(self):
        """Anular pago"""
        self.payment_status = "VOID"