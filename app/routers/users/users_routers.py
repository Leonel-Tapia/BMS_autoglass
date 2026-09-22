# /app/routers/users/users_routers.py | Updated: 2026-07-20 21:54
# Core router for the Users module: handles Login, List, Create, Edit, and Secure Update.

from fastapi import APIRouter, Depends, HTTPException, Request, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
import math
from datetime import datetime

from app.database.database import get_db
from app.models.company.user import User 

# 🔥 IMPORTACIÓN CORRECTA DEL LOADER
from app.core.template_loader import jinja as templates


router = APIRouter(prefix="/users", tags=["users"])

# ---------------------------------------------------------
# LOGIN (Redirección oficial a /auth/login)
# ---------------------------------------------------------
@router.get("/login")
def redirect_login():
    return RedirectResponse(url="/auth/login", status_code=303)

# ---------------------------------------------------------
# LISTADO DE USUARIOS
# ---------------------------------------------------------
@router.get("/list", response_class=HTMLResponse)
def list_users(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    search: str = Query(""),
    role: str = Query(""),
    active: str = Query("")
):
    query = db.query(User)
    if search:
        query = query.filter(
            or_(
                User.full_name.ilike(f"%{search}%"),
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )
    if role:
        query = query.filter(User.role == role)
    if active == "true":
        query = query.filter(User.is_active == True)
    elif active == "false":
        query = query.filter(User.is_active == False)

    query = query.order_by(User.full_name.asc())

    total_count = query.count()
    total_pages = math.ceil(total_count / limit) if total_count > 0 else 1
    offset = (page - 1) * limit
    users_data = query.offset(offset).limit(limit).all()

    return templates.TemplateResponse(
        request=request,
        name="users/user_list.html",
        context={
            "users": users_data, "page": page,            "total_pages": total_pages,
            "limit": limit, "search": search, "role": role, "active": active
        }
    )

# ---------------------------------------------------------
# CREAR USUARIO (Carga de formulario)
# ---------------------------------------------------------
@router.get("/create", response_class=HTMLResponse)
def get_create_user(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="users/user_create.html",
        context={}
    )

# ---------------------------------------------------------
# CREAR USUARIO (Procesar datos del Formulario Compacto)
# ---------------------------------------------------------
@router.post("/create")
def post_create_user(
    full_name: str = Form(...),
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    position: str = Form(None),
    salary: float = Form(0.0),
    hire_date: str = Form(None),
    is_active: str = Form("true"),
    address: str = Form(None),
    city: str = Form(None),
    state: str = Form(None),
    postal_code: str = Form(None),
    phone_1: str = Form(None),
    db: Session = Depends(get_db)
):
    try:
        h_date = None
        if hire_date:
            try:
                h_date = datetime.strptime(hire_date, '%Y-%m-%d')
            except ValueError:
                h_date = None

        new_user = User(
            full_name=full_name,
            username=username,
            email=email,
            password=password, 
            role=role,
            position=position,
            salary=salary,
            hire_date=h_date,
            is_active=(is_active == "true"),
            address=address,
            city=city,
            state=state,
            postal_code=postal_code,
            phone_1=phone_1
        )
        db.add(new_user)
        db.commit()
        print(f"INFO: Usuario {username} creado con éxito.")
        return RedirectResponse(url="/users/list", status_code=303)
    except Exception as e:
        db.rollback()
        print(f"ERROR CRÍTICO AL CREAR: {e}")
        return RedirectResponse(url="/users/create?error=true", status_code=303)

# ---------------------------------------------------------
# EDITAR USUARIO (Carga de datos)
# ---------------------------------------------------------
@router.get("/edit/{user_id}", response_class=HTMLResponse)
def get_edit_user(request: Request, user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(url="/users/list", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="users/user_edit.html",
        context={"user": user}
    )

# ---------------------------------------------------------
# ACTUALIZAR USUARIO
# ---------------------------------------------------------
@router.post("/update/{user_id}")
def post_update_user(
    user_id: int,
    full_name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    is_active: str = Form(...),
    password: str = Form(None),
    address: str = Form(None),
    city: str = Form(None),
    state: str = Form(None),
    postal_code: str = Form(None),
    phone_1: str = Form(None),
    phone_2: str = Form(None),
    position: str = Form(None),
    salary: float = Form(0.0),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.id == user_id).first()
    
    if not db_user:
        return RedirectResponse(url="/users/list?error=notfound", status_code=303)

    try:
        db_user.full_name = full_name
        db_user.email = email
        db_user.role = role
        db_user.is_active = (is_active == "true")
        db_user.address = address
        db_user.city = city
        db_user.state = state
        db_user.postal_code = postal_code
        db_user.phone_1 = phone_1
        db_user.phone_2 = phone_2
        db_user.position = position
        db_user.salary = salary

        if password and password.strip():
            db_user.password = password 

        db.commit()
        print(f"INFO: Usuario {user_id} actualizado exitosamente.")
        
    except Exception as e:
        db.rollback()
        print(f"ERROR: Fallo en actualización de ID {user_id}: {str(e)}")
        return RedirectResponse(url=f"/users/edit/{user_id}?error=db", status_code=303)

    return RedirectResponse(url="/users/list", status_code=303)

# ---------------------------------------------------------
# ELIMINAR USUARIO
# ---------------------------------------------------------
@router.post("/delete/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            db.delete(user)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"ERROR al eliminar: {e}")
        
    return RedirectResponse(url="/users/list", status_code=303)