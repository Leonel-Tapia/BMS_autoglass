# RUTA: app/models/call_center/invoices_model.py
# FECHA: 2026-07-15 13:50 MDT
# DESCRIPCIÓN: Acceso a facturas reales para Call Center (NO define tablas)

from sqlalchemy.orm import Session
from app.models.invoices.invoice_model import Invoice


def get_invoices_by_customer(db: Session, customer_id: int):
    """
    Retorna todas las facturas reales del cliente usando el modelo oficial.
    """
    return db.query(Invoice).filter(
        Invoice.customer_id == customer_id
    ).all()


def get_invoice_details(db: Session, invoice_id: int):
    """
    Retorna una factura específica.
    """
    return db.query(Invoice).filter(
        Invoice.id == invoice_id
    ).first()
