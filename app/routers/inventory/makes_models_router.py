# RUTA: app/routers/inventory/makes_models_router.py | ACTUALIZADO: 2026-07-21
# DESCRIPCIÓN: Router unificado para la gestión de Makes, Models y Trims en el panel Manager

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.inventory.make_model import VehicleMake
from app.models.inventory.vehicle_model_model import VehicleModel
from app.models.inventory.vehicle_trim_model import VehicleTrim
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/manager/makesmodels", tags=["manager-makes-models"])
templates = Jinja2Templates(directory="app/templates")

# 1. VISTA PRINCIPAL (LISTAR Y FILTRAR LAS 3 COLUMNAS)
@router.get("/list")
def makes_models_list(
    request: Request, 
    make_id: int = None, 
    model_id: int = None, 
    db: Session = Depends(get_db)
):
    # Cargar todas las marcas
    makes = db.query(VehicleMake).order_by(VehicleMake.make.asc()).all()
    
    # Cargar modelos según la marca seleccionada
    models = []
    if make_id:
        models = db.query(VehicleModel).filter(VehicleModel.make_id == make_id).order_by(VehicleModel.model.asc()).all()
        
    # Cargar trims según el modelo seleccionado
    trims = []
    if model_id:
        trims = db.query(VehicleTrim).filter(VehicleTrim.model_id == model_id).order_by(VehicleTrim.trim.asc()).all()

    return templates.TemplateResponse(
        request,
        "manager/modules/makes_models/makes_models_list.html",  # Ruta corregida según la estructura de directorios
        {
            "makes": makes,
            "models": models,
            "trims": trims,
            "selected_make_id": make_id,
            "selected_model_id": model_id
        }
    )


# 2. GUARDAR MARCA (MAKE)
@router.post("/add_make")
def add_make(make_name: str = Form(...), db: Session = Depends(get_db)):
    make_name_clean = make_name.strip()
    if make_name_clean:
        exists = db.query(VehicleMake).filter(VehicleMake.make.ilike(make_name_clean)).first()
        if not exists:
            new_make = VehicleMake(make=make_name_clean)
            db.add(new_make)
            db.commit()
            db.refresh(new_make)
            # Redirigir seleccionando la nueva marca recién creada
            return RedirectResponse(url=f"/manager/makesmodels/list?make_id={new_make.id}", status_code=303)
            
    return RedirectResponse(url="/manager/makesmodels/list", status_code=303)


# 3. GUARDAR MODELO (MODEL)
@router.post("/add_model")
def add_model(
    make_id: int = Form(...), 
    model_name: str = Form(...), 
    db: Session = Depends(get_db)
):
    model_name_clean = model_name.strip()
    if make_id and model_name_clean:
        exists = db.query(VehicleModel).filter(
            VehicleModel.make_id == make_id, 
            VehicleModel.model.ilike(model_name_clean)
        ).first()
        
        if not exists:
            new_model = VehicleModel(make_id=make_id, model=model_name_clean)
            db.add(new_model)
            db.commit()
            db.refresh(new_model)
            # Redirigir manteniendo la marca y seleccionando el nuevo modelo
            return RedirectResponse(url=f"/manager/makesmodels/list?make_id={make_id}&model_id={new_model.id}", status_code=303)
            
    return RedirectResponse(url=f"/manager/makesmodels/list?make_id={make_id}", status_code=303)


# 4. GUARDAR TRIM (TRIM)
@router.post("/add_trim")
def add_trim(
    make_id: int = Form(None),
    model_id: int = Form(...), 
    trim_name: str = Form(...), 
    db: Session = Depends(get_db)
):
    trim_name_clean = trim_name.strip()
    if model_id and trim_name_clean:
        exists = db.query(VehicleTrim).filter(
            VehicleTrim.model_id == model_id, 
            VehicleTrim.trim.ilike(trim_name_clean)
        ).first()
        
        if not exists:
            new_trim = VehicleTrim(model_id=model_id, trim=trim_name_clean)
            db.add(new_trim)
            db.commit()
            
    # Redirigir manteniendo la selección actual de marca y modelo
    query_params = f"model_id={model_id}"
    if make_id:
        query_params = f"make_id={make_id}&" + query_params
        
    return RedirectResponse(url=f"/manager/makesmodels/list?{query_params}", status_code=303)