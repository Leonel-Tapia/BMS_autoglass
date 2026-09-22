# RUTA: app/routers/users/auth_login.py
# ACTUALIZADO: 2026-09-04

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.company.user import User
from app.models.company.company import Company
from app.core.template_loader import jinja as templates

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_company_name(db: Session):
    company = db.query(Company).first()
    return company.trade_name if company else "BMS Autoglass"


def redirect_by_role(role: str):
    role = role.strip().lower()

    if role == "admin":
        return "/company/main_menu"

    if role == "sales":
        return "/call_center/menu"

    if role == "manager":
        return "/company/main_menu"

    if role == "technician":
        return "/technician/dashboard"

    return "/company/main_menu"


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    company_name = get_company_name(db)
    return templates.TemplateResponse(
        request=request,
        name="users/login.html",
        context={"company_name": company_name}
    )


@router.post("/login")
def login_action(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    company_name = get_company_name(db)
    user = db.query(User).filter(User.username == username).first()

    if not user or user.password != password:
        return templates.TemplateResponse(
            request=request,
            name="users/login.html",
            context={"error": "Invalid credentials", "company_name": company_name}
        )

    if not user.is_active:
        return templates.TemplateResponse(
            request=request,
            name="users/login.html",
            context={"error": "User account is disabled", "company_name": company_name}
        )

    # PROCESAR ROL CORRECTAMENTE
    user_role_clean = str(user.role).strip().lower()

    # USAR EL CAMPO CORRECTO DEL MODELO
    user_full_name = user.full_name

    # GUARDAR USUARIO EN SESIÓN
    request.session["user_id"] = user.id
    request.session["user_name"] = user_full_name
    request.session["username"] = user.username
    request.session["role"] = user_role_clean

    print(f"DEBUG: Login exitoso para '{username}'. Rol crudo: '{user.role}'. Rol procesado: '{user_role_clean}'")

    redirect_url = redirect_by_role(user_role_clean)
    print(f"INFO: Redirigiendo a {redirect_url} para: {username}")

    return RedirectResponse(url=redirect_url, status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/auth/login", status_code=303)