# /app/routers/manager/manager_menu.py | Updated: 2026-08-27

from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

# IMPORTACIÓN CORRECTA DEL LOADER
from app.core.template_loader import jinja as templates
from app.database.database import SessionLocal

# ✅ USAR EL MODELO EXISTENTE
from app.models.invoices.invoice_activity_model import Concept

router = APIRouter(prefix="/manager", tags=["Manager"])

# ============================================================
# RUTAS EXISTENTES
# ============================================================

@router.get("/menu")
def manager_menu(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="manager/manager_menu.html",
        context={}
    )

@router.get("/windshield_menu")
def windshield_menu(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="manager/windshield_menu.html",
        context={}
    )


# ============================================================
# ⭐ NUEVAS RUTAS: ACTIVITY CONCEPTS
# ============================================================

@router.get("/activities_concepts")
def activities_concepts(request: Request):
    """Página para gestionar conceptos de actividades"""
    return templates.TemplateResponse(
        request=request,
        name="manager/activities_concepts.html",
        context={}
    )


# ============================================================
# DEPENDENCIA PARA BASE DE DATOS
# ============================================================

def get_db():
    """Obtener una sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# API ENDPOINTS PARA CONCEPTOS
# ============================================================

@router.get("/api/concepts")
def get_concepts(db: Session = Depends(get_db)):
    """Obtener todos los conceptos activos"""
    try:
        concepts = db.query(Concept).filter(Concept.is_active == True).order_by(Concept.sort_order, Concept.name).all()
        return {
            'success': True,
            'data': [c.to_dict() for c in concepts]
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': str(e)}
        )


@router.get("/api/concepts/all")
def get_all_concepts(db: Session = Depends(get_db)):
    """Obtener todos los conceptos (incluyendo inactivos)"""
    try:
        concepts = db.query(Concept).order_by(Concept.sort_order, Concept.name).all()
        return {
            'success': True,
            'data': [c.to_dict() for c in concepts]
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': str(e)}
        )


@router.post("/api/concepts")
async def create_concept(request: Request, db: Session = Depends(get_db)):
    """Crear un nuevo concepto"""
    try:
        form = await request.form()
        name = form.get('name')
        is_active = form.get('is_active') == 'true'
        
        if not name:
            return JSONResponse(
                status_code=400,
                content={'success': False, 'error': 'Name is required'}
            )
        
        # Obtener el último sort_order
        last = db.query(Concept).order_by(Concept.sort_order.desc()).first()
        sort_order = (last.sort_order + 1) if last else 0
        
        concept = Concept(
            name=name,
            is_active=is_active,
            sort_order=sort_order,
            created_by='admin'
        )
        db.add(concept)
        db.commit()
        db.refresh(concept)
        
        return {'success': True, 'data': concept.to_dict()}
    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': str(e)}
        )


@router.put("/api/concepts/{concept_id}")
async def update_concept(request: Request, concept_id: int, db: Session = Depends(get_db)):
    """Actualizar un concepto existente"""
    try:
        form = await request.form()
        concept = db.query(Concept).filter(Concept.id == concept_id).first()
        if not concept:
            return JSONResponse(
                status_code=404,
                content={'success': False, 'error': 'Concept not found'}
            )
        
        name = form.get('name')
        is_active = form.get('is_active') == 'true'
        
        if not name:
            return JSONResponse(
                status_code=400,
                content={'success': False, 'error': 'Name is required'}
            )
        
        concept.name = name
        concept.is_active = is_active
        db.commit()
        db.refresh(concept)
        
        return {'success': True, 'data': concept.to_dict()}
    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': str(e)}
        )


@router.delete("/api/concepts/{concept_id}")
def delete_concept(concept_id: int, db: Session = Depends(get_db)):
    """Eliminar un concepto"""
    try:
        concept = db.query(Concept).filter(Concept.id == concept_id).first()
        if not concept:
            return JSONResponse(
                status_code=404,
                content={'success': False, 'error': 'Concept not found'}
            )
        
        db.delete(concept)
        db.commit()
        
        return {'success': True}
    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': str(e)}
        )