# LOGIN /app/models/company/user.py | Updated: 2026-05-06 09:12
# User model for authentication and user management.

from sqlalchemy import Column, Integer, Text, Boolean, TIMESTAMP, Float
from app.database.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(Text, nullable=False)
    username = Column(Text, nullable=False, unique=True)
    password = Column(Text, nullable=False)
    email = Column(Text, nullable=False, unique=True)

    address = Column(Text, nullable=True)
    city = Column(Text, nullable=True)
    state = Column(Text, nullable=True)
    postal_code = Column(Text, nullable=True)
    country = Column(Text, nullable=True)
    location = Column(Text, nullable=True)

    phone_1 = Column(Text, nullable=True)
    phone_2 = Column(Text, nullable=True)

    role = Column(Text, nullable=False)

    position = Column(Text, nullable=True)
    salary = Column(Float, nullable=True)
    hire_date = Column(TIMESTAMP, nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
