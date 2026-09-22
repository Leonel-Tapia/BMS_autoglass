# RUTA: app/services/call_center/call_center_service.py
# FECHA: 2026-07-20 08:35 MDT

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, Table
from app.models.customers.customer_model import Customer
from app.models.invoices.invoice_model import Invoice
from app.models.estimates.estimate_model import Estimate

class CallCenterService:
    def __init__(self, db: Session):
        self.db = db

    def search_customers_dynamic(self, name: str = "", phone: str = ""):
        clean_phone = "".join(filter(str.isdigit, phone))
        
        query = self.db.query(Customer)
        filters = []

        if name:
            filters.append(Customer.name.ilike(f"%{name}%"))

        if clean_phone:
            def clean_db_col(col):
                return func.regexp_replace(col, '[^0-9]', '', 'g')
            
            filters.append(
                or_(
                    clean_db_col(Customer.phone).contains(clean_phone),
                    clean_db_col(Customer.phone2).contains(clean_phone),
                    clean_db_col(Customer.contact_phone).contains(clean_phone),
                    clean_db_col(Customer.contact_phone2).contains(clean_phone)
                )
            )

        if not filters:
            return []

        return query.filter(and_(*filters)).all()

    def get_customer_details(self, customer_id: int):
        return self.db.query(Customer).filter(Customer.id == customer_id).first()

    def get_customer_history(self, customer_id: int):
        invoices = self.db.query(Invoice).filter(Invoice.customer_id == customer_id).all()
        
        vehicle_years = Table('vehicle_years', Estimate.metadata, autoload_with=self.db.get_bind())
        
        estimates = self.db.query(Estimate, vehicle_years.c.year).outerjoin(
            vehicle_years, Estimate.vehicle_year_id == vehicle_years.c.id
        ).filter(
            Estimate.customer_id == customer_id
        ).order_by(
            Estimate.date_request.desc(), 
            Estimate.id.desc()
        ).all()
        
        return {"invoices": invoices, "estimates": estimates}

    def get_estimate_details(self, estimate_id: int):
        # Cargamos la tabla dinámicamente para acceder a estimate_details
        estimate_details = Table('estimate_details', Estimate.metadata, autoload_with=self.db.get_bind())
        
        # Consultamos todos los productos/servicios para ese ID de estimado
        return self.db.query(estimate_details).filter(
            estimate_details.c.estimate_id == estimate_id
        ).all()