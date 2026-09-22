# ============================================================
# RUTA: app/routers/purchases/purchase_router.py
# ACTUALIZADO: 2026-06-16
# DESCRIPCIÓN: Router consolidado con VOID PO (delete) agregado.
# ============================================================

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
import datetime

from app.database.database import get_db 
from app.models.vendors.vendor_model import Vendor 
from app.models.purchases.purchase_model import PurchaseOrder, PurchaseOrderDetail
from app.models.purchases.purchase_order_receiving import PurchaseOrderReceiving
from app.models.inventory.inventory import InventoryPart 

router = APIRouter(prefix="/purchases", tags=["Purchases"])
templates = Jinja2Templates(directory="app/templates")

# ============================================================
# 1. VISTA DE CREACIÓN
# ============================================================
@router.get("/create", response_class=HTMLResponse)
def create_purchase_order_view(request: Request, vendor_id: int = None, db: Session = Depends(get_db)):
    vendor_data = db.query(Vendor).filter(Vendor.id == vendor_id).first() if vendor_id else None
    parts_catalog = db.query(InventoryPart).filter(InventoryPart.is_active == True).all()
    return templates.TemplateResponse(
        request=request, 
        name="purchases/purchase_create.html", 
        context={"title": "New PO", "vendor": vendor_data, "parts_catalog": parts_catalog}
    )

# ============================================================
# 2. GUARDAR PO (DRAFT)
# ============================================================
@router.post("/save-draft")
async def save_purchase_order_draft(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()

        # VALIDACIÓN DE DUPLICADOS
        raw_lines = data.get("lines", []) or []
        part_numbers = [
            (str(line.get("part_number") or "").strip().lower())
            for line in raw_lines
            if (line.get("part_number") or "").strip() != ""
        ]
        if len(part_numbers) != len(set(part_numbers)):
            return JSONResponse(
                status_code=400,
                content={"message": "Duplicate part numbers are not allowed."}
            )

        # CREAR ENCABEZADO
        new_po = PurchaseOrder(
            po_number=f"PO-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
            po_date=data.get("order_date") or datetime.date.today(),
            vendor_id=data.get("vendor_id"),
            vendor_invoice_number=data.get("vendor_invoice_number", ""),
            status="DRAFT",
            shipping_handling=Decimal(str(data.get("shipping_handling", 0))),
            tax_amount=Decimal(str(data.get("tax_amount", 0))),
            internal_notes=data.get("internal_notes", "")
        )
        db.add(new_po)
        db.flush()
        
        # CALCULAR TOTAL LÍNEAS
        lines_total = sum([
            Decimal(str(line.get("quantity_ordered", 0))) * Decimal(str(line.get("unit_cost", 0)))
            for line in data.get("lines", [])
        ])
        new_po.grand_total = lines_total + new_po.tax_amount + new_po.shipping_handling
        
        # CREAR DETALLES
        for line in data.get("lines", []):
            qty = Decimal(str(line.get("quantity_ordered", 0)))
            cost = Decimal(str(line.get("unit_cost", 0)))
            detail = PurchaseOrderDetail(
                purchase_order_id=new_po.id,
                part_number=line.get("part_number"),
                item_description=line.get("item_description"),
                quantity_ordered=qty,
                unit_cost=cost,
                line_subtotal=qty * cost
            )
            db.add(detail)

        db.commit()
        return {"status": "success", "po_number": new_po.po_number}

    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"message": str(e)})

# ============================================================
# 3. VISTA DE PO (VIEW)
# ============================================================
@router.get("/view/{po_id}", response_class=HTMLResponse)
def view_purchase_order(request: Request, po_id: int, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")

    po.details.sort(key=lambda d: (d.part_number or "").lower())
    vendor = db.query(Vendor).filter(Vendor.id == po.vendor_id).first()

    return templates.TemplateResponse(
        request=request,
        name="purchases/purchase_view.html",
        context={
            "title": f"PO Detail: {po.po_number}",
            "po": po,
            "vendor": vendor
        }
    )

# ============================================================
# 4. VISTA DE EDICIÓN
# ============================================================
@router.get("/edit/{po_id}", response_class=HTMLResponse)
def edit_purchase_order_view(request: Request, po_id: int, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")

    po.details.sort(key=lambda d: (d.part_number or "").lower())
    vendor = db.query(Vendor).filter(Vendor.id == po.vendor_id).first()
    parts_catalog = db.query(InventoryPart).filter(InventoryPart.is_active == True).all()

    return templates.TemplateResponse(
        request=request,
        name="purchases/purchase_edit.html",
        context={
            "title": f"Edit PO: {po.po_number}",
            "po": po,
            "vendor": vendor,
            "parts_catalog": parts_catalog
        }
    )

# ============================================================
# 5. ACTUALIZAR PO
# ============================================================
@router.post("/update/{po_id}")
async def update_purchase_order(po_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        if not po:
            return JSONResponse(status_code=404, content={"message": "PO not found"})
        
        form_data = await request.form()

        po.po_date = form_data.get("order_date") or po.po_date
        po.status = form_data.get("status")
        po.vendor_invoice_number = form_data.get("vendor_invoice_number", po.vendor_invoice_number)
        po.shipping_handling = Decimal(form_data.get("shipping_handling", 0))
        po.tax_amount = Decimal(form_data.get("tax_amount", 0))
        po.internal_notes = form_data.get("internal_notes", "")

        # LEER TODAS LAS LÍNEAS
        lines = {}
        for key, value in form_data.items():
            if key.startswith("details["):
                idx = key.split("[")[1].split("]")[0]
                field = key.split("[")[2].split("]")[0]
                if idx not in lines:
                    lines[idx] = {}
                lines[idx][field] = value

        # VALIDACIÓN DE DUPLICADOS
        part_numbers = [
            (data.get("part_number") or "").strip().lower()
            for data in lines.values()
        ]
        if len(part_numbers) != len(set(part_numbers)):
            return JSONResponse(
                status_code=400,
                content={"message": "Duplicate part numbers are not allowed."}
            )

        # ACTUALIZAR LÍNEAS EXISTENTES
        existing_details = po.details
        for i, detail in enumerate(existing_details):
            if str(i) in lines:
                data = lines[str(i)]
                detail.part_number = data.get("part_number", detail.part_number)
                detail.item_description = data.get("item_description", detail.item_description)
                detail.quantity_ordered = Decimal(data.get("quantity_ordered", detail.quantity_ordered))
                detail.unit_cost = Decimal(data.get("unit_cost", detail.unit_cost))
                detail.line_subtotal = detail.quantity_ordered * detail.unit_cost

        # AGREGAR NUEVAS LÍNEAS
        existing_count = len(existing_details)
        for idx, data in lines.items():
            if int(idx) >= existing_count:
                qty = Decimal(data.get("quantity_ordered", 0))
                cost = Decimal(data.get("unit_cost", 0))
                new_detail = PurchaseOrderDetail(
                    purchase_order_id=po.id,
                    part_number=data.get("part_number"),
                    item_description=data.get("item_description"),
                    quantity_ordered=qty,
                    unit_cost=cost,
                    line_subtotal=qty * cost
                )
                db.add(new_detail)

        db.flush()

        # ORDEN AUTOMÁTICO
        po.details.sort(key=lambda d: (d.part_number or "").lower())

        # RECALCULAR TOTAL
        lines_total = sum([d.line_subtotal for d in po.details])
        po.grand_total = lines_total + po.tax_amount + po.shipping_handling
        
        db.commit()
        return RedirectResponse(url=f"/purchases/view/{po_id}", status_code=303)

    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"message": str(e)})

# ============================================================
# 6. ACEPTAR PO
# ============================================================
@router.post("/accept/{po_id}")
def accept_purchase_order(po_id: int, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")

    po.status = "ACCEPTED"
    db.commit()

    return RedirectResponse(url=f"/purchases/view/{po_id}", status_code=303)

# ============================================================
# 7. DETALLE DE PO
# ============================================================
@router.get("/detail/{po_id}", response_class=HTMLResponse)
def purchase_order_detail(request: Request, po_id: int, db: Session = Depends(get_db)):

    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")

    vendor = db.query(Vendor).filter(Vendor.id == po.vendor_id).first()

    po_details = (
        db.query(PurchaseOrderDetail)
        .filter(PurchaseOrderDetail.purchase_order_id == po_id)
        .order_by(PurchaseOrderDetail.part_number.asc())
        .all()
    )

    subtotal = sum(d.line_subtotal for d in po_details)
    tax = po.tax_amount or 0
    shipping = po.shipping_handling or 0
    grand_total = subtotal + tax + shipping

    return templates.TemplateResponse(
        request=request,
        name="purchases/purchase_order_detail.html",
        context={
            "title": f"PO Detail: {po.po_number}",
            "po": po,
            "vendor": vendor,
            "po_details": po_details,
            "subtotal": subtotal,
            "tax": tax,
            "shipping": shipping,
            "grand_total": grand_total
        }
    )

# ============================================================
# 8. VOID PO (DELETE REAL)
# ============================================================
@router.post("/void/{po_id}")
def void_purchase_order(po_id: int, db: Session = Depends(get_db)):

    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")

    # Solo se puede borrar si está en DRAFT
    if po.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Only DRAFT POs can be deleted")

    vendor_id = po.vendor_id

    # Borrar detalles primero
    db.query(PurchaseOrderDetail).filter(
        PurchaseOrderDetail.purchase_order_id == po_id
    ).delete()

    # Borrar encabezado
    db.delete(po)
    db.commit()

    # Redirigir al historial del vendor
    return RedirectResponse(
        url=f"/vendors/po-history/{vendor_id}",
        status_code=303
    )

# ============================================================
# 9. VOID RECEIVING (RESET PO TO DRAFT)
# ============================================================
@router.post("/void-receiving/{po_id}")
def void_purchase_order_receiving(po_id: int, db: Session = Depends(get_db)):

    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")

    # Solo aplica si el PO está en ACCEPTED / PARTIAL / RECEIVED
    if po.status not in ["ACCEPTED", "PARTIAL", "RECEIVED"]:
        raise HTTPException(
            status_code=400,
            detail="VOID RECEIVING only allowed for ACCEPTED / PARTIAL / RECEIVED POs"
        )

    # Obtener todos los receivings NO void de este PO
    receivings = (
        db.query(PurchaseOrderReceiving)
        .filter(PurchaseOrderReceiving.purchase_order_id == po_id)
        .filter(PurchaseOrderReceiving.is_void == False)
        .all()
    )

    if not receivings:
        raise HTTPException(
            status_code=400,
            detail="No active receivings found for this PO"
        )

    # Marcar todos los receivings como VOID
    for rec in receivings:
        rec.is_void = True
        rec.void_reason = "VOID RECEIVING"
        rec.updated_at = func.now()
        rec.updated_by = "system"

    # Regresar el PO a DRAFT
    po.status = "DRAFT"

    # Agregar nota automática
    note = "VOID RECEIVING"
    if po.internal_notes:
        po.internal_notes = f"{po.internal_notes}\n{note}"
    else:
        po.internal_notes = note

    db.commit()

    return RedirectResponse(
        url=f"/purchases/view/{po_id}",
        status_code=303
    )
