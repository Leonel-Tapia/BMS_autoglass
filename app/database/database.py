# /app/database/database.py | Updated: 2026-09-22
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# If a DATABASE_URL env var exists (cloud), use it; otherwise use local DB
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:leotap@localhost:5432/BMS_Autoglass_DB"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Get DB session in routers
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()