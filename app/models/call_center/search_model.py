# RUTA: app/models/call_center/search_model.py
# FECHA: 2026-07-15 13:45 MDT
# DESCRIPCIÓN: Funciones de búsqueda para Call Center (SIN definir tablas)

from sqlalchemy.orm import Session
from app.models.customers.customer_model import Customer


def search_customer(db: Session, phone: str = "", name: str = "", lastname: str = ""):
    """
    Búsqueda de clientes para el módulo Call Center.
    Usa el modelo REAL de customers sin redefinir la tabla.
    """

    query = db.query(Customer)

    # 🔍 Búsqueda por teléfono
    if phone:
        query = query.filter(Customer.phone == phone)

    # 🔍 Búsqueda por nombre
    if name:
        query = query.filter(Customer.name.ilike(f"%{name}%"))

    # 🔍 Tu tabla NO tiene last_name, así que se ignora
    customer = query.first()

    if not customer:
        return None

    # Convertir a dict para JSON
    return {
        "id": customer.id,
        "name": customer.name,
        "business_name": customer.business_name,
        "contact_name": customer.contact_name,
        "contact_phone": customer.contact_phone,
        "phone": customer.phone,
        "phone2": customer.phone2,
        "email": customer.email,
        "address": customer.address,
        "city": customer.city,
        "state": customer.state,
        "zip_code": customer.zip_code,
        "customer_type": customer.customer_type,
        "mood": customer.mood,
        "customer_rating": customer.customer_rating,
        "status": customer.status,
        "internal_notes": customer.internal_notes,
        "last_purchase_date": customer.last_purchase_date,
        "updated_at": customer.updated_at,
    }
