from sqlalchemy import Column, Integer, String, Boolean, Text, Numeric, DateTime
from sqlalchemy.sql import func
from app.database.database import Base

class Company(Base):
    __tablename__ = "company"

    id = Column(Integer, primary_key=True, index=True)
    trade_name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=False)
    tax_id = Column(String(50), unique=True, index=True)
    business_line = Column(String(255))
    address = Column(String(255))
    neighborhood = Column(String(100))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    main_phone = Column(String(50))
    main_email = Column(String(100))
    contact_name = Column(String(100))
    contact_phone = Column(String(50))
    contact_email = Column(String(100))
    notes = Column(Text)
    invoice_notice = Column(Text)
    is_active = Column(Boolean, default=True)
    general_sales_tax = Column(Numeric(10, 2), default=0.00)
    
    # Nuevos campos agregados
    mobile_fee = Column(Numeric(10, 2), default=0.00)
    labor_cost = Column(Numeric(10, 2), default=0.00)
    materials_cost = Column(Numeric(10, 2), default=0.00)
    misc_cost = Column(Numeric(10, 2), default=0.00)

    # CAMBIO 2026-09-14: punto de partida para optimización de ruta
    origin_address = Column(Text, nullable=True)
     
    registration_date = Column(DateTime(timezone=True), server_default=func.now())