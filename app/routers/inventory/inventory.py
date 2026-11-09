# /app/routers/inventory/inventory.py
# Solución definitiva al error de columna generada (PostgreSQL) + Gestión (Manage)
# Fecha: 2026-07-20

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.purchases.purchase_model import PurchaseOrderDetail
from app.models.invoices.invoice_model import InvoiceItem
from decimal import Decimal
from typing import Optional

# Importamos la base de datos y el modelo
from app.database.database import get_db
from app.models.inventory.inventory import InventoryPart
from app.models.inventory.windshield_catalog_model import WindshieldCatalog

router = APIRouter(prefix="/inventory", tags=["inventory"])
templates = Jinja2Templates(directory="app/templates")

# --- VISTAS (HTML) ---

@router.get("/view/catalogo", response_class=HTMLResponse)
async def view_catalogo(request: Request):
    return templates.TemplateResponse(request=request, name="inventory/inventory_catalogo.html")

@router.get("/view/create", response_class=HTMLResponse)
async def view_create_part(request: Request):
    return templates.TemplateResponse(request=request, name="inventory/inventory_create.html")

@router.get("/view/edit/{sku}", response_class=HTMLResponse)
async def view_edit_part(sku: str, request: Request, db: Session = Depends(get_db)):
    """Carga la vista de gestión para una parte específica"""
    part = db.query(InventoryPart).filter(InventoryPart.sku == sku).first()
    if not part:
        # Si no existe, redirigimos al catálogo o lanzamos error
        raise HTTPException(status_code=404, detail="La parte no existe")
    return templates.TemplateResponse(
        request=request, 
        name="inventory/inventory_edit.html", 
        context={"part": part}
    )

# --- API (ACCIONES) ---

@router.post("/create")
async def create_inventory_part(request: Request, db: Session = Depends(get_db)):
    try:
        form_data = await request.json()
        sku_val = form_data.get("sku")
        
        if not sku_val:
            raise HTTPException(status_code=400, detail="El SKU es obligatorio.")
            
        if db.query(InventoryPart).filter(InventoryPart.sku == sku_val).first():
            raise HTTPException(status_code=400, detail=f"El SKU {sku_val} ya existe.")

        part_data = {
            "sku": sku_val,
            "part_number": form_data.get("part_number"),
            "part_name": form_data.get("part_name"),
            "description": form_data.get("description"),
            "quantity_on_hand": int(form_data.get("quantity_on_hand") or 0),
            "minimum_quantity": int(form_data.get("minimum_quantity") or 0),
            "location": form_data.get("location"),
            "unit_cost": Decimal(str(form_data.get("unit_cost") or "0.00")),
            "unit_sale": Decimal(str(form_data.get("unit_sale") or "0.00")),
            "is_active": form_data.get("is_active", True)
        }

        max_val = form_data.get("maximum_quantity")
        if max_val and str(max_val).strip():
            part_data["maximum_quantity"] = int(max_val)

        new_part = InventoryPart(**part_data)
        db.add(new_part)
        db.commit()
        return {"status": "success", "message": "Parte registrada exitosamente"}

    except Exception as e:
        db.rollback()
        print(f"DEBUG CRÍTICO CREATE: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno de base de datos")

@router.post("/update/{old_sku}")
async def update_inventory_part(old_sku: str, request: Request, db: Session = Depends(get_db)):
    """Actualiza una parte existente sin tocar total_cost"""
    try:
        form_data = await request.json()
        part = db.query(InventoryPart).filter(InventoryPart.sku == old_sku).first()

        if not part:
            raise HTTPException(status_code=404, detail="Registro no encontrado")

        # Actualización de campos (SKU se mantiene fijo para integridad)
        part.part_number = form_data.get("part_number")
        part.part_name = form_data.get("part_name")
        part.description = form_data.get("description")
        part.location = form_data.get("location")
        part.quantity_on_hand = int(form_data.get("quantity_on_hand") or 0)
        part.minimum_quantity = int(form_data.get("minimum_quantity") or 0)
        part.unit_cost = Decimal(str(form_data.get("unit_cost") or "0.00"))
        part.unit_sale = Decimal(str(form_data.get("unit_sale") or "0.00"))
        part.is_active = form_data.get("is_active", True)

        max_val = form_data.get("maximum_quantity")
        part.maximum_quantity = int(max_val) if max_val and str(max_val).strip() else None

        db.commit()
        return {"status": "success", "message": "Parte actualizada correctamente"}

    except Exception as e:
        db.rollback()
        print(f"DEBUG CRÍTICO UPDATE: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al actualizar")

@router.get("/list")
async def list_parts(db: Session = Depends(get_db)):
    # Subconsultas para entradas (Compras) y salidas (Facturas)
    entradas_subq = db.query(
        PurchaseOrderDetail.part_number,
        func.sum(PurchaseOrderDetail.quantity_ordered).label('total_in')
    ).group_by(PurchaseOrderDetail.part_number).subquery()

    salidas_subq = db.query(
        InvoiceItem.part_number,
        func.sum(InvoiceItem.quantity).label('total_out')
    ).group_by(InvoiceItem.part_number).subquery()

    # Consulta principal cruzando WindshieldCatalog con movimientos
    query = db.query(
        WindshieldCatalog,
        func.coalesce(entradas_subq.c.total_in, 0).label('total_in'),
        func.coalesce(salidas_subq.c.total_out, 0).label('total_out')
    ).outerjoin(
        entradas_subq, WindshieldCatalog.nags_code == entradas_subq.c.part_number
    ).outerjoin(
        salidas_subq, WindshieldCatalog.nags_code == salidas_subq.c.part_number
    ).order_by(WindshieldCatalog.nags_code.asc())

    result = []
    for catalog_item, total_in, total_out in query.all():
        total_in = float(total_in)
        total_out = float(total_out)
        stock = total_in - total_out

        # L?gica: Mostrar si stock > 0 o si hubo movimientos (entradas/salidas)
        if stock > 0 or total_in > 0 or total_out > 0:
            result.append({
                "id": catalog_item.id,
                "sku": catalog_item.nags_code,
                "part_number": catalog_item.nags_code,
                "part_name": catalog_item.description,
                "description": catalog_item.description,
                "quantity_on_hand": int(stock),
                "minimum_quantity": 0,
                "unit_cost": float(catalog_item.cost) if catalog_item.cost else 0.00,
                "unit_sale": float(catalog_item.price) if catalog_item.price else 0.00,
                "total_cost": float(stock * catalog_item.cost) if catalog_item.cost else 0.00,
                "is_active": True
            })
    return result