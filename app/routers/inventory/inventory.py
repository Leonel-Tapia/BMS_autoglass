# /app/routers/inventory/inventory.py
# Solución definitiva al error de columna generada (PostgreSQL) + Gestión (Manage)
# Fecha: 2026-07-20

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Optional

# Importamos la base de datos y el modelo
from app.database.database import get_db
from app.models.inventory.inventory import InventoryPart

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
    return db.query(InventoryPart).order_by(InventoryPart.part_number.asc()).all()