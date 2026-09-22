from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Asegúrate de importar tu sesión de base de datos, el modelo de estimado y el nuevo historial
# from app.database import get_db
# from app.models.estimates.estimate_model import Estimate
# from app.models.estimates.estimate_history_model import EstimatesHistory

router = APIRouter(prefix="/call_center", tags=["Call Center Estimates"])


class EstimateHistoryCreate(BaseModel):
  estimate_id: int
  action_type: str
  message: Optional[str] = None
  created_by: str


@router.get("/estimates/{estimate_id}/history")
def get_estimate_history(estimate_id: int, db: Session = Depends(get_db)):
  """Obtiene el historial completo de auditoría para un estimado específico."""
  history = (
      db.query(EstimatesHistory)
      .filter(EstimatesHistory.estimate_id == estimate_id)
      .order_by(EstimatesHistory.created_at.desc())
      .all()
  )
  return history


@router.post("/estimates/history", status_code=status.HTTP_201_CREATED)
def create_estimate_history(
    data: EstimateHistoryCreate, db: Session = Depends(get_db)
):
  """Registra una nueva acción del call center y actualiza el estado si aplica."""
  new_history = EstimatesHistory(
      estimate_id=data.estimate_id,
      action_type=data.action_type,
      message=data.message,
      created_by=data.created_by,
      created_at=datetime.utcnow(),
  )
  db.add(new_history)

  # Si la acción es confirmar sin cambios, actualizamos el estado en la tabla estimates
  if data.action_type == "Confirmed":
    estimate = db.query(Estimate).filter(Estimate.id == data.estimate_id).first()
    if estimate:
      estimate.status = "Confirmed"

  db.commit()
  db.refresh(new_history)

  return {
      "success": True,
      "message": "Historial registrado correctamente.",
      "id": new_history.id,
  }