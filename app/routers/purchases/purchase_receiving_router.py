# ============================================================
# FILE: app/routers/purchases/purchase_receiving_router.py
# UPDATED: 2026-06-16 (INVENTORY MOVEMENTS INTEGRATED)
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi.templating import Jinja2Templates
from decimal import Decimal

from app.database.database import get_db
from app.models.purchases.purchase_model import PurchaseOrder, PurchaseOrderDetail
from app.models.purchases.purchase_order_receiving import PurchaseOrderReceiving
from app.models.vendors.vendor_model import Vendor
from app.models.inventory.inventory import InventoryPart
from app.models.inventory.inventory_movement import InventoryMovement  # 👈 NUEVO

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# ============================================================
# GET /receiving/{po_id}
# ============================================================
@router.get("/receiving/{po_id}")
def receiving_screen(po_id: int, request: Request, db: Session = Depends(get_db)):

    po = (
        db.query(PurchaseOrder, Vendor.vendor_name)
        .join(Vendor, Vendor.id == PurchaseOrder.vendor_id)
        .filter(PurchaseOrder.id == po_id)
        .first()
    )

    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    po_data = po.PurchaseOrder
    vendor_name = po.vendor_name

    details = (
        db.query(PurchaseOrderDetail)
        .filter(PurchaseOrderDetail.purchase_order_id == po_id)
        .all()
    )

    rows = []
    for d in details:
        received_total = (
            db.query(PurchaseOrderReceiving)
            .filter(PurchaseOrderReceiving.purchase_order_detail_id == d.id)
            .filter(PurchaseOrderReceiving.is_void == False)
            .with_entities(func.coalesce(func.sum(PurchaseOrderReceiving.received_qty), 0))
            .scalar()
        ) or 0

        remaining = float(d.quantity_ordered) - float(received_total)

        rows.append({
            "detail_id": d.id,
            "part_number": d.part_number,
            "description": d.item_description,
            "ordered_qty": float(d.quantity_ordered),
            "received_total": float(received_total),
            "remaining_qty": float(remaining),
            "unit_cost": float(d.unit_cost),
        })

    total_ordered = sum([float(r["ordered_qty"]) for r in rows])
    total_received = sum([float(r["received_total"]) for r in rows])
    total_remaining = sum([float(r["remaining_qty"]) for r in rows])

    percent_complete = 0
    if total_ordered > 0:
        percent_complete = round((total_received / total_ordered) * 100, 2)

    status_badge = po_data.status

    context = {
        "po": po_data,
        "po_id": po_id,
        "vendor_id": po_data.vendor_id,
        "vendor_name": vendor_name,
        "rows": rows,
        "total_ordered": total_ordered,
        "total_received": total_received,
        "total_remaining": total_remaining,
        "percent_complete": percent_complete,
        "status_badge": status_badge
    }

    return templates.TemplateResponse(
        request=request,
        name="purchases/purchase_receiving_view.html",
        context=context
    )

# ============================================================
# POST /receiving/save/{po_id}
# ============================================================
@router.post("/receiving/save/{po_id}")
def save_receiving(po_id: int, data: dict, db: Session = Depends(get_db)):

    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    rows = data.get("rows", [])
    user = data.get("user", "system")

    if not rows:
        raise HTTPException(status_code=400, detail="No receiving data provided")

    for r in rows:
        detail_id = r.get("detail_id")
        qty = float(r.get("received_qty", 0) or 0)

        if qty <= 0:
            continue

        detail = db.query(PurchaseOrderDetail).filter(PurchaseOrderDetail.id == detail_id).first()
        if not detail:
            raise HTTPException(status_code=404, detail=f"Detail {detail_id} not found")

        received_total = (
            db.query(PurchaseOrderReceiving)
            .filter(PurchaseOrderReceiving.purchase_order_detail_id == detail_id)
            .filter(PurchaseOrderReceiving.is_void == False)
            .with_entities(func.coalesce(func.sum(PurchaseOrderReceiving.received_qty), 0))
            .scalar()
        ) or 0

        remaining = float(detail.quantity_ordered) - float(received_total)

        if qty > remaining:
            raise HTTPException(
                status_code=400,
                detail=f"Received qty {qty} exceeds remaining qty {remaining} for detail {detail_id}",
            )

        rec = PurchaseOrderReceiving(
            purchase_order_id=po_id,
            purchase_order_detail_id=detail_id,
            received_qty=qty,
            received_by=user,
            created_by=user,
            condition="OK",
        )
        db.add(rec)

        item = db.query(InventoryPart).filter(InventoryPart.part_number == detail.part_number).first()
        if item:
            item.quantity_on_hand += qty
            item.total_cost += qty * float(detail.unit_cost)

            # 👇 INVENTORY MOVEMENT (IN)
            movement = InventoryMovement(
                part_id=item.id,
                movement_type="IN",
                quantity=Decimal(str(qty)),
                unit_cost=Decimal(str(detail.unit_cost)),
                total_cost=Decimal(str(qty)) * Decimal(str(detail.unit_cost)),
                reference_type="PO",
                reference_id=po_id,
                created_by=user
            )
            db.add(movement)

    db.flush()

    all_details = (
        db.query(PurchaseOrderDetail)
        .filter(PurchaseOrderDetail.purchase_order_id == po_id)
        .all()
    )

    fully_received = True
    for d in all_details:
        received_total = (
            db.query(PurchaseOrderReceiving)
            .filter(PurchaseOrderReceiving.purchase_order_detail_id == d.id)
            .filter(PurchaseOrderReceiving.is_void == False)
            .with_entities(func.coalesce(func.sum(PurchaseOrderReceiving.received_qty), 0))
            .scalar()
        ) or 0

        if float(received_total) < float(d.quantity_ordered):
            fully_received = False
            break

    po.status = "RECEIVED" if fully_received else "PARTIAL"

    db.commit()
    db.refresh(po)

    return {"status": "success", "message": "Receiving saved successfully"}

# ============================================================
# POST /purchase-receiving/receive-selected
# ============================================================
@router.post("/purchase-receiving/receive-selected")
async def receive_selected(request: Request, db: Session = Depends(get_db)):

    data = await request.json()
    po_id = data.get("po_id")
    items = data.get("items", [])

    if not items:
        return {"status": "error", "msg": "No items received"}

    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        return {"status": "error", "msg": "PO not found"}

    for item in items:
        detail_id = int(item["po_detail_id"])
        qty = float(item["qty"])

        detail = db.query(PurchaseOrderDetail).filter_by(id=detail_id).first()
        if not detail:
            return {"status": "error", "msg": f"Detail {detail_id} not found"}

        received_total = (
            db.query(PurchaseOrderReceiving)
            .filter(PurchaseOrderReceiving.purchase_order_detail_id == detail_id)
            .filter(PurchaseOrderReceiving.is_void == False)
            .with_entities(func.coalesce(func.sum(PurchaseOrderReceiving.received_qty), 0))
            .scalar()
        ) or 0

        remaining = float(detail.quantity_ordered) - float(received_total)

        if qty > remaining:
            return {"status": "error", "msg": f"Overreceive on detail {detail_id}"}

        rec = PurchaseOrderReceiving(
            purchase_order_id=po_id,
            purchase_order_detail_id=detail_id,
            received_qty=qty,
            received_by="system",
            created_by="system",
            condition="OK",
        )
        db.add(rec)

        item_inv = db.query(InventoryPart).filter(InventoryPart.part_number == detail.part_number).first()
        if item_inv:
            item_inv.quantity_on_hand += qty
            item_inv.total_cost += Decimal(str(qty)) * Decimal(str(detail.unit_cost))

            # 👇 INVENTORY MOVEMENT (IN)
            movement = InventoryMovement(
                part_id=item_inv.id,
                movement_type="IN",
                quantity=Decimal(str(qty)),
                unit_cost=Decimal(str(detail.unit_cost)),
                total_cost=Decimal(str(qty)) * Decimal(str(detail.unit_cost)),
                reference_type="PO",
                reference_id=po_id,
                created_by="system"
            )
            db.add(movement)

    db.flush()

    all_details = (
        db.query(PurchaseOrderDetail)
        .filter(PurchaseOrderDetail.purchase_order_id == po_id)
        .all()
    )

    fully_received = True
    for d in all_details:
        received_total = (
            db.query(PurchaseOrderReceiving)
            .filter(PurchaseOrderReceiving.purchase_order_detail_id == d.id)
            .filter(PurchaseOrderReceiving.is_void == False)
            .with_entities(func.coalesce(func.sum(PurchaseOrderReceiving.received_qty), 0))
            .scalar()
        ) or 0

        if float(received_total) < float(d.quantity_ordered):
            fully_received = False
            break

    po.status = "RECEIVED" if fully_received else "PARTIAL"

    db.commit()
    db.refresh(po)

    return {"status": "ok"}
