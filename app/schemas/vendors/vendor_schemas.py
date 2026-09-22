# RUTA: app/schemas/vendors/vendor_schemas.py
# ACTUALIZADO: 2026-05-15 11:15
# DESCRIPCIÓN: Esquemas de Pydantic para validación de datos de proveedores (Vendors)

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VendorBase(BaseModel):
    vendor_code: Optional[str] = None
    vendor_name: str
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    tax_id: Optional[str] = None
    payment_terms: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True

class VendorCreate(VendorBase):
    """Esquema para la creación de nuevos proveedores"""
    pass

class VendorResponse(VendorBase):
    """Esquema para la visualización y respuesta de datos"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True