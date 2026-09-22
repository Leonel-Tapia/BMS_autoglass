# /app/routers/inventory/years_router.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.manager.modules.years.years_model import Years
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
import datetime

router = APIRouter(prefix="/manager/years", tags=["years"])
templates = Jinja2Templates(directory="app/templates")

# LIST YEARS
@router.get("/list")
def years_list(request: Request, db: Session = Depends(get_db)):
    years = db.query(Years).order_by(Years.year.desc()).all()
    
    max_year_db = db.query(func.max(Years.year)).scalar()
    current_real_year = datetime.datetime.now().year
    
    # Límite: Permitir hasta 3 años por encima del año actual real (Ej: 2026 + 3 = 2029)
    max_allowed_year = current_real_year + 3

    if max_year_db:
        next_year = max_year_db + 1
    else:
        next_year = current_real_year

    # Bandera para saber si rebasamos el límite permitido
    disable_add = False
    if next_year > max_allowed_year:
        next_year = max_allowed_year
        disable_add = True

    return templates.TemplateResponse(
        request,
        "manager/modules/years/years_list.html",
        {
            "years": years, 
            "next_year": next_year, 
            "disable_add": disable_add,
            "max_allowed_year": max_allowed_year
        }
    )


# SAVE YEAR
@router.post("/add")
def years_add(request: Request, db: Session = Depends(get_db)):
    max_year_db = db.query(func.max(Years.year)).scalar()
    current_real_year = datetime.datetime.now().year
    max_allowed_year = current_real_year + 3

    if max_year_db:
        next_year = max_year_db + 1
    else:
        next_year = current_real_year

    # Validación estricta en servidor por seguridad
    if next_year > max_allowed_year:
        return RedirectResponse("/manager/years/list", status_code=303)

    exists = db.query(Years).filter(Years.year == next_year).first()
    if exists:
        return RedirectResponse("/manager/years/list", status_code=303)

    new_year = Years(year=next_year)
    db.add(new_year)
    db.commit()

    return RedirectResponse("/manager/years/list", status_code=303)