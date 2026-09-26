# /app/routers/insurance/insurance_companies_router.py | Created: 2026-09-26
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional

from app.database.database import get_db
from app.core.template_loader import jinja as templates
from app.models.invoices.insurance_company_model import InsuranceCompany


router = APIRouter(
    prefix="/insurance/companies",
    tags=["insurance_companies"]
)


# ============================================================
# 1. LIST ALL COMPANIES
# ============================================================
@router.get("", response_class=HTMLResponse)
def insurance_companies_list(
    request: Request,
    search: str = "",
    db: Session = Depends(get_db)
):
    query = db.query(InsuranceCompany)
    if search:
        query = query.filter(InsuranceCompany.name.ilike(f"%{search}%"))
    companies = query.order_by(InsuranceCompany.name.asc()).all()

    user_role = request.session.get("role", "").strip().lower()

    return templates.TemplateResponse(
        request=request,
        name="insurance/companies_list.html",
        context={
            "companies": companies,
            "search": search,
            "user_role": user_role,
        }
    )


# ============================================================
# 2. JSON ENDPOINT (para dropdowns en invoice_view)
# ============================================================
@router.get("/json")
def insurance_companies_json(db: Session = Depends(get_db)):
    companies = db.query(InsuranceCompany).filter(
        InsuranceCompany.is_active == True
    ).order_by(InsuranceCompany.name.asc()).all()

    return JSONResponse(content=[
        {
            "id": c.id,
            "name": c.name,
            "phone": c.phone,
            "email": c.email,
        }
        for c in companies
    ])


# ============================================================
# 3. ADD FORM (GET)
# ============================================================
@router.get("/add", response_class=HTMLResponse)
def insurance_companies_add_form(
    request: Request,
    return_url: Optional[str] = None,
    db: Session = Depends(get_db)
):
    user_role = request.session.get("role", "").strip().lower()
    if user_role not in ["admin", "manager"]:
        return RedirectResponse("/insurance/companies", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="insurance/companies_add.html",
        context={
            "company": None,
            "return_url": return_url,
            "user_role": user_role,
        }
    )


# ============================================================
# 4. ADD FORM (POST)
# ============================================================
@router.post("/add")
def insurance_companies_add(
    request: Request,
    name: str = Form(...),
    phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    is_active: Optional[str] = Form(None),
    return_url: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    user_role = request.session.get("role", "").strip().lower()
    if user_role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    name_clean = (name or "").strip()
    if not name_clean:
        raise HTTPException(status_code=400, detail="Name is required")

    existing = db.query(InsuranceCompany).filter(InsuranceCompany.name == name_clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="An insurance company with this name already exists")

    new_company = InsuranceCompany(
        name=name_clean,
        phone=(phone or "").strip() or None,
        email=(email or "").strip() or None,
        address=(address or "").strip() or None,
        notes=(notes or "").strip() or None,
        is_active=(str(is_active).lower() in ["on", "true", "1"]) if is_active is not None else True,
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)

    if return_url and return_url != "None":
        return RedirectResponse(url=return_url, status_code=303)
    return RedirectResponse(url="/insurance/companies", status_code=303)


# ============================================================
# 5. EDIT FORM (GET)
# ============================================================
@router.get("/edit/{company_id}", response_class=HTMLResponse)
def insurance_companies_edit_form(
    company_id: int,
    request: Request,
    return_url: Optional[str] = None,
    db: Session = Depends(get_db)
):
    user_role = request.session.get("role", "").strip().lower()
    if user_role not in ["admin", "manager"]:
        return RedirectResponse("/insurance/companies", status_code=303)

    company = db.query(InsuranceCompany).filter(InsuranceCompany.id == company_id).first()
    if not company:
        return RedirectResponse("/insurance/companies", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="insurance/companies_edit.html",
        context={
            "company": company,
            "return_url": return_url,
            "user_role": user_role,
        }
    )


# ============================================================
# 6. EDIT FORM (POST)
# ============================================================
@router.post("/edit/{company_id}")
def insurance_companies_edit(
    company_id: int,
    request: Request,
    name: str = Form(...),
    phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    is_active: Optional[str] = Form(None),
    return_url: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    user_role = request.session.get("role", "").strip().lower()
    if user_role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    company = db.query(InsuranceCompany).filter(InsuranceCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Insurance company not found")

    name_clean = (name or "").strip()
    if not name_clean:
        raise HTTPException(status_code=400, detail="Name is required")

    # Validar nombre único (excepto la misma empresa)
    existing = db.query(InsuranceCompany).filter(
        InsuranceCompany.name == name_clean,
        InsuranceCompany.id != company_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Another insurance company with this name already exists")

    company.name = name_clean
    company.phone = (phone or "").strip() or None
    company.email = (email or "").strip() or None
    company.address = (address or "").strip() or None
    company.notes = (notes or "").strip() or None
    company.is_active = (str(is_active).lower() in ["on", "true", "1"]) if is_active is not None else False

    db.commit()

    if return_url and return_url != "None":
        return RedirectResponse(url=return_url, status_code=303)
    return RedirectResponse(url="/insurance/companies", status_code=303)


# ============================================================
# 7. DELETE (soft delete = marcar inactivo)
# ============================================================
@router.post("/delete/{company_id}")
def insurance_companies_delete(
    company_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user_role = request.session.get("role", "").strip().lower()
    if user_role not in ["admin"]:
        raise HTTPException(status_code=403, detail="Only admin can delete insurance companies")

    company = db.query(InsuranceCompany).filter(InsuranceCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Insurance company not found")

    # Soft delete: solo marcamos is_active = false
    company.is_active = False
    db.commit()

    return RedirectResponse(url="/insurance/companies", status_code=303)