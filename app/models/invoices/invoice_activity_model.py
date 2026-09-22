# /app/models/invoices/invoice_activity_model.py
from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base


class Concept(Base):
    __tablename__ = "concepts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_by = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relación con actividades
    activities = relationship("InvoiceActivity", backref="concept")

    def __repr__(self):
        return f"<Concept(id={self.id}, name={self.name})>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "is_active": self.is_active,
            "sort_order": self.sort_order,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class InvoiceActivity(Base):
    __tablename__ = "invoice_activities"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relación con Invoice
    invoice = relationship("Invoice", backref="activities")

    def __repr__(self):
        return f"<InvoiceActivity(id={self.id}, invoice_id={self.invoice_id}, concept_id={self.concept_id})>"

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "concept_id": self.concept_id,
            "concept_name": self.concept.name if self.concept else None,
            "description": self.description,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }