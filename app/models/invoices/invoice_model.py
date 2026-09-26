# /app/models/invoices/invoice_model.py | Updated: 2026-09-26 (insurance fields)
from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, Date, TIMESTAMP, Text, Boolean, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    estimate_id = Column(Integer, ForeignKey("estimates.id", ondelete="SET NULL"), index=True, unique=True, nullable=True)
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
    tentative_time = Column(TIMESTAMP, nullable=True)
    
    # Auditoría y Estado
    operator_username = Column(String(50))
    created_by = Column(String(100))
    created_at = Column(TIMESTAMP)
    authorized_by = Column(String(50))
    auth_date_time = Column(TIMESTAMP)
    status = Column(String(20), default="Invoice", index=True)
    invoice_number = Column(String(50))
    language = Column(String(20), default="English")
    
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
    
    # --- TÉCNICO ASIGNADO ---
    technician_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    notes = Column(Text)

    # --- CAMPOS DE GARANTÍA (WARRANTY) ---
    is_warranty = Column(Boolean, default=False, nullable=False)
    warranty_reference_invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True)
    warranty_start_date = Column(Date, nullable=True)
    warranty_end_date = Column(Date, nullable=True)
    warranty_notes = Column(Text, nullable=True)

    # --- CAMPOS DE ASEGURADORA (INSURANCE) ---
    insurance_company_id = Column(Integer, ForeignKey("insurance_companies.id", ondelete="SET NULL"), nullable=True, index=True)
    insurance_claim_number = Column(String(100), nullable=True)
    insurance_adjuster_name = Column(String(200), nullable=True)
    insurance_adjuster_phone = Column(String(50), nullable=True)
    insurance_adjuster_email = Column(String(200), nullable=True)
    insurance_claim_date = Column(Date, nullable=True)
    insurance_amount = Column(DECIMAL(10, 2), default=0.00)
    insurance_status = Column(String(30), nullable=True)
    customer_amount = Column(DECIMAL(10, 2), default=0.00)

    # Relaciones
    technician = relationship("User", foreign_keys=[technician_id])
    items = relationship("InvoiceItem", backref="invoice", cascade="all, delete-orphan")
    estimate = relationship("Estimate", backref="invoice", uselist=False)

    # Relación self-referencial: invoice actual → invoice original (si es garantía)
    warranty_reference_invoice = relationship(
        "Invoice",
        remote_side=[id],
        foreign_keys=[warranty_reference_invoice_id]
    )

    # Relación con aseguradora
    insurance_company = relationship("InsuranceCompany", foreign_keys=[insurance_company_id])


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), index=True)
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