# RUTA: app/models/customers/customer_model.py
# ARCHIVO: customer_model.py
# ACTUALIZADO: 2026-06-23 20:10 MDT
# DESCRIPCIÓN: Customer model aligned with DB table (100% match)

from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric, Date, TIMESTAMP, Float, func
from app.database.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)

    # ============================
    # MAIN FIELDS
    # ============================
    name = Column(String(150), nullable=False)
    business_name = Column(String(150))

    contact_name = Column(String(150))
    contact_phone = Column(String(20))
    contact_phone_numeric = Column(String(20))  # <-- NUEVO CAMPO
    
    contact_name2 = Column(String(150))
    contact_phone2 = Column(String(20))
    contact_phone2_numeric = Column(String(20)) # <-- NUEVO CAMPO
    
    contact_relationship = Column(String(100))

    phone = Column(String(20))
    phone_numeric = Column(String(20))          # <-- NUEVO CAMPO
    
    phone2 = Column(String(20))
    phone2_numeric = Column(String(20))         # <-- NUEVO CAMPO

    email = Column(String(150))

    address = Column(Text)
    city = Column(String(100))
    state = Column(String(2))
    zip_code = Column(String(5))

    # ============================
    # GEOCODING FIELDS (NUEVOS)
    # ============================
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    tax_id = Column(String(50))
    language = Column(String(20))
    customer_type = Column(String(50))
    mood = Column(String(20))
    status = Column(String(20), default="ACTIVE")

    internal_notes = Column(Text)

    # ============================
    # ADDITIONAL INFORMATION
    # ============================
    allow_sms = Column(Boolean, default=True)
    sms_opt_out_reason = Column(String(150))

    preferred_contact_method = Column(String(50))
    preferred_contact = Column(String(50))

    referral_source = Column(String(150))
    tags = Column(String(200))

    birthday = Column(Date)
    last_purchase_date = Column(Date)

    credit_limit = Column(Numeric, default=0)
    customer_rating = Column(Integer)

    is_tax_exempt = Column(Boolean, default=False)
    tax_exempt = Column(String(10))
    tax_exempt_license = Column(String(100))

    # ============================
    # TIMESTAMPS
    # ============================
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())