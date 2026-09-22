# RUTA: app/models/call_center/estimates_model.py
# FECHA: 2026-07-15 13:55 MDT
# DESCRIPCIÓN: Modelo de lectura para Call Center (NO define tablas)

from sqlalchemy.orm import Session
from app.models.estimates.estimate_model import Estimate, EstimateDetail


def get_estimates_by_customer(db: Session, customer_id: int):
    """
    Retorna todos los estimados reales del cliente usando el modelo oficial.
    """
    return db.query(Estimate).filter(
        Estimate.customer_id == customer_id
    ).all()


def get_estimate_details(db: Session, estimate_id: int):
    """
    Retorna los detalles reales del estimado.
    """
    return db.query(EstimateDetail).filter(
        EstimateDetail.estimate_id == estimate_id
    ).all()
