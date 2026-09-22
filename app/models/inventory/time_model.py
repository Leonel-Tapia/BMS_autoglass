from sqlalchemy import Column, Integer, String, Time
from app.database.database import Base

class TimeCatalog(Base):
    __tablename__ = 'time_catalog'

    id = Column(Integer, primary_key=True, index=True)
    time_value = Column(Time, nullable=False)
    display_time = Column(String(10), nullable=False)

    def __repr__(self):
        return f"<TimeCatalog(display_time='{self.display_time}')>"