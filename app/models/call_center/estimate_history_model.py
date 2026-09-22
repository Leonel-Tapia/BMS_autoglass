# /app/models/call_center/estimate_history_model.py

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text
from app.database.database import Base


class EstimatesHistory(Base):
    __tablename__ = "estimates_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    estimate_id = Column(Integer, nullable=False, index=True)
    action_type = Column(String, nullable=False)
    message = Column(Text, nullable=True)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)