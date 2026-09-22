# /app/models/estimates/estimate_model.py | Updated: 07-22-2026
from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, Date, TIMESTAMP, Text, Boolean, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base

class Estimate(Base):
    __tablename__ = "estimates"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False, index=True)
    vehicle_year_id = Column(Integer, ForeignKey("vehicle_years.id"), index=True)
    vehicle_vin = Column(String(17))

    # Vehículo
    vehicle_make = Column(String(50))
    vehicle_model = Column(String(50))

    # Ubicación y tipo de servicio
    glass_type = Column(String(20))
    window_position = Column(String(30))
    service_type = Column(String(50), nullable=False)
    customer_address = Column(String(255))
    
    # Fechas y Citas
    date_request = Column(Date, default=func.current_date())
    time_created = Column(TIMESTAMP, server_default=func.now())
    estimated_appointment_date = Column(Date)
    estimated_appointment_time = Column(Time) 
    
    # Auditoría y Estado
    operator_username = Column(String(50))
    authorized_by = Column(String(50))
    auth_date_time = Column(TIMESTAMP)
    status = Column(String(20), default="Estimate", index=True)
    invoice_number = Column(Integer)
    language = Column(String(20), default="English")
    
    # --- CAMPOS DE ANULACIÓN (VOID) ---
    void_reason = Column(Text)
    voided_at = Column(TIMESTAMP)
    voided_by = Column(String(50))
    
    # Totales
    subtotal = Column(DECIMAL(12, 2), default=0.00)
    tax = Column(DECIMAL(12, 2), default=0.00)
    total = Column(DECIMAL(12, 2), default=0.00)
    
    # Costos
    labor_cost = Column(DECIMAL(12, 2), default=0.00)
    materials_cost = Column(DECIMAL(12, 2), default=0.00)
    misc_cost = Column(DECIMAL(12, 2), default=0.00)
    mobile_fee_override = Column(Boolean, default=False)
    special_discount = Column(DECIMAL(12, 2), default=0.00)
    special_discount_reason = Column(String(100))
    
    # --- CAMPOS DE CONTACTO ALTERNATIVO ---
    alt_contact_name = Column(String(100))
    alt_contact_phone = Column(String(20))
    alt_contact_relation = Column(String(50))
    
    # --- CAMPOS DE PAGO ---
    payment_method1 = Column(String(50))
    payment_amount1 = Column(DECIMAL(12, 2), default=0.00)
    payment_method2 = Column(String(50))
    payment_amount2 = Column(DECIMAL(12, 2), default=0.00)
    payment_status = Column(String(20), default="PENDING")
    
    notes = Column(Text)

    # Relaciones
    details = relationship("EstimateDetail", backref="estimate", cascade="all, delete-orphan")


class EstimateDetail(Base):
    __tablename__ = "estimate_details"

    id = Column(Integer, primary_key=True, index=True)
    estimate_id = Column(Integer, ForeignKey("estimates.id", ondelete="CASCADE"), index=True)
    product_name = Column(String(255), nullable=False)
    description = Column(String(255))
    quantity = Column(Integer, nullable=False)
    part_number = Column(String(100))
    supplier = Column(String(100))
    cost = Column(DECIMAL(12, 2))
    price = Column(DECIMAL(12, 2), nullable=False)
    is_taxable = Column(Boolean, default=True)
    tax_amount = Column(DECIMAL(12, 2), default=0.00)
    
    # Logística
    is_received = Column(Boolean, default=False)
    received_by = Column(String(100))
    received_at = Column(TIMESTAMP)