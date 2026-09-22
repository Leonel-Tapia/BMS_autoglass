# RUTA: app/models/vendors/vendor_model.py
# ACTUALIZADO: 2026-06-13
# DESCRIPCIÓN: Modelo Vendor actualizado con campo terms_days (Integer)

from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, func
from app.database.database import Base 

class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    vendor_code = Column(String(50))
    vendor_name = Column(String(200), nullable=False)
    
    # Contacto
    contact_name = Column(String(200))
    contact_title = Column(String(100))
    phone = Column(String(50))
    mobile = Column(String(50))
    email = Column(String(200))
    
    # Ubicación
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    zip_code = Column(String(20))
    
    # Otros
    tax_id = Column(String(100))
    payment_terms = Column(String(100))

    # ⭐ NUEVO CAMPO — requerido por Purchase Orders
    terms_days = Column(Integer, default=0)

    website = Column(String(200))
    notes = Column(Text)
    
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())
