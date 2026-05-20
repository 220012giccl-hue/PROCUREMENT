from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from config.database import get_db
from database.models import ProcurementItem, RFQ, Supplier, SupplierQuote, AuditLog
from typing import List, Optional, Dict
from datetime import datetime

router = APIRouter(prefix="/api/procurement", tags=["procurement"])

@router.post("/save")
async def save_to_procurement_list(
    item_data: Dict = Body(...),
    db: Session = Depends(get_db)
):
    """Saves a product or material to the user's procurement list with supplier mapping"""
    try:
        supplier_name = item_data.get('supplier')
        supplier_id = None
        
        if supplier_name and supplier_name.strip():
            stripped_name = supplier_name.strip()
            # Try to find existing supplier
            existing_sup = db.query(Supplier).filter(Supplier.name.ilike(stripped_name)).first()
            if existing_sup:
                supplier_id = existing_sup.id
            else:
                # Create a new supplier
                new_sup = Supplier(
                    name=stripped_name,
                    contact_person="Sales Representative",
                    notes="Created automatically from AI Procurement research."
                )
                db.add(new_sup)
                db.commit()
                db.refresh(new_sup)
                supplier_id = new_sup.id

        new_item = ProcurementItem(
            item_name=item_data.get('item_name'),
            category=item_data.get('category'),
            supplier_id=supplier_id,
            quantity=item_data.get('quantity'),
            estimated_cost=item_data.get('estimated_cost'),
            source_url=item_data.get('source_url'),
            technical_notes=item_data.get('technical_notes'),
            ai_recommendation=item_data.get('ai_recommendation'),
            status='RESEARCHING'
        )
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        
        # Log action
        log = AuditLog(
            action="SAVE_TO_LIST",
            agent="PROCUREMENT_AGENT",
            details={"item_id": new_item.id, "item_name": new_item.item_name}
        )
        db.add(log)
        db.commit()
        
        return {"success": True, "item_id": new_item.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rfq/create")
async def create_rfq(
    rfq_data: Dict = Body(...),
    db: Session = Depends(get_db)
):
    """Creates a new RFQ record and prepares it for sending"""
    try:
        # Generate RFQ number
        count = db.query(RFQ).count()
        rfq_no = f"RFQ-{datetime.now().year}-{count + 1001}"
        
        status = rfq_data.get('status', 'DRAFT')
        
        new_rfq = RFQ(
            rfq_number=rfq_no,
            procurement_item_id=rfq_data.get('item_id'), # Optional if coming from direct card
            quantity=rfq_data.get('quantity'),
            delivery_location=rfq_data.get('delivery_location', 'Main Warehouse'),
            required_delivery_date=datetime.fromisoformat(rfq_data.get('required_date')) if rfq_data.get('required_date') else None,
            technical_requirements=rfq_data.get('specs'),
            status=status
        )
        
        # Store extra info in technical requirements or notes if needed
        # For simplicity, we use the model's existing fields
        
        db.add(new_rfq)
        db.commit()
        db.refresh(new_rfq)
        
        # Log action
        log = AuditLog(
            action="CREATE_RFQ",
            agent="PROCUREMENT_AGENT",
            details={"rfq_id": new_rfq.id, "rfq_no": rfq_no, "status": status}
        )
        db.add(log)
        db.commit()
        
        return {"success": True, "rfq_number": rfq_no, "id": new_rfq.id}
    except Exception as e:
        db.rollback()
        import logging
        logging.error(f"RFQ Creation Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def get_procurement_list(db: Session = Depends(get_db)):
    """Retrieves all items in the procurement list with supplier name joined"""
    items = db.query(ProcurementItem).order_by(ProcurementItem.created_at.desc()).all()
    result = []
    for i in items:
        supplier_name = None
        if i.supplier_id:
            sup = db.query(Supplier).filter(Supplier.id == i.supplier_id).first()
            supplier_name = sup.name if sup else None
        
        # Self-healing mapping: If supplier is missing, infer it from the source_url
        if not supplier_name and i.source_url:
            inferred = None
            url_lower = i.source_url.lower()
            if "bunnings" in url_lower:
                inferred = "Bunnings"
            elif "sydneytools" in url_lower:
                inferred = "Sydney Tools"
            elif "blackwoods" in url_lower:
                inferred = "Blackwoods"
            elif "mitre10" in url_lower:
                inferred = "Mitre 10"
            elif "totaltools" in url_lower:
                inferred = "Total Tools"
            elif "ebay" in url_lower:
                inferred = "eBay"
            elif "amazon" in url_lower:
                inferred = "Amazon"
                
            if inferred:
                try:
                    # Find or create supplier
                    sup = db.query(Supplier).filter(Supplier.name.ilike(inferred)).first()
                    if not sup:
                        sup = Supplier(
                            name=inferred,
                            contact_person="Sales Representative",
                            notes="Automatically created from source URL mapping."
                        )
                        db.add(sup)
                        db.commit()
                        db.refresh(sup)
                    
                    i.supplier_id = sup.id
                    db.commit()
                    supplier_name = inferred
                except Exception as db_err:
                    db.rollback()
                    print(f"Error self-healing supplier: {db_err}")
                    # Fallback to returning the inferred name anyway
                    supplier_name = inferred

        result.append({
            "id": i.id,
            "item_name": i.item_name,
            "category": i.category,
            "status": i.status,
            "approval_status": i.approval_status,
            "technical_notes": i.technical_notes,
            "source_url": i.source_url,
            "quantity": i.quantity,
            "estimated_cost": i.estimated_cost,
            "supplier": supplier_name,
            "ai_recommendation": i.ai_recommendation,
            "created_at": i.created_at.isoformat()
        })
    return {"success": True, "data": result}

@router.get("/rfqs")
async def get_rfq_list(db: Session = Depends(get_db)):
    """Retrieves all RFQs with supplier name joined"""
    rfqs = db.query(RFQ).order_by(RFQ.created_at.desc()).all()
    result = []
    for r in rfqs:
        supplier_name = None
        if r.supplier_id:
            sup = db.query(Supplier).filter(Supplier.id == r.supplier_id).first()
            supplier_name = sup.name if sup else None
        result.append({
            "id": r.id,
            "rfq_number": r.rfq_number,
            "status": r.status,
            "quantity": r.quantity,
            "delivery_location": r.delivery_location,
            "required_delivery_date": r.required_delivery_date.isoformat() if r.required_delivery_date else None,
            "technical_requirements": r.technical_requirements,
            "email_subject": r.email_subject,
            "supplier": supplier_name,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        })
    return {"success": True, "data": result}

@router.get("/rfqs/{rfq_id}")
async def get_rfq_detail(rfq_id: int, db: Session = Depends(get_db)):
    """Retrieves a single RFQ by ID"""
    r = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="RFQ not found")
    supplier_name = None
    supplier_email = None
    if r.supplier_id:
        sup = db.query(Supplier).filter(Supplier.id == r.supplier_id).first()
        if sup:
            supplier_name = sup.name
            supplier_email = sup.email
    return {
        "id": r.id,
        "rfq_number": r.rfq_number,
        "status": r.status,
        "quantity": r.quantity,
        "delivery_location": r.delivery_location,
        "required_delivery_date": r.required_delivery_date.isoformat() if r.required_delivery_date else None,
        "technical_requirements": r.technical_requirements,
        "email_subject": r.email_subject,
        "email_body": r.email_body,
        "supplier": supplier_name,
        "supplier_email": supplier_email,
        "created_at": r.created_at.isoformat(),
    }

@router.patch("/rfqs/{rfq_id}/status")
async def update_rfq_status(rfq_id: int, data: Dict = Body(...), db: Session = Depends(get_db)):
    """Updates the status of an RFQ"""
    r = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="RFQ not found")
    new_status = data.get("status")
    if new_status:
        r.status = new_status
        db.commit()
        log = AuditLog(action="UPDATE_RFQ_STATUS", agent="PROCUREMENT_AGENT",
                       details={"rfq_id": rfq_id, "new_status": new_status})
        db.add(log)
        db.commit()
    return {"success": True}

@router.delete("/{id}")
async def delete_procurement_item(id: int, db: Session = Depends(get_db)):
    """Deletes an item from the procurement list"""
    try:
        item = db.query(ProcurementItem).filter(ProcurementItem.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        db.delete(item)
        db.commit()
        return {"success": True, "message": "Item deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# --- Supplier Management ---

@router.get("/suppliers", response_model=List[Dict])
async def get_suppliers(db: Session = Depends(get_db)):
    """Retrieves all suppliers"""
    suppliers = db.query(Supplier).order_by(Supplier.name).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "contact_person": s.contact_person,
            "email": s.email,
            "phone": s.phone,
            "website": s.website,
            "categories": s.categories,
            "location": s.location,
            "rating": s.rating,
            "preferred_supplier": s.preferred_supplier,
            "notes": s.notes
        } for s in suppliers
    ]

@router.post("/suppliers")
async def add_supplier(
    data: Dict = Body(...),
    db: Session = Depends(get_db)
):
    """Adds a new supplier"""
    try:
        new_supplier = Supplier(
            name=data.get('name'),
            contact_person=data.get('contact_person'),
            email=data.get('email'),
            phone=data.get('phone'),
            website=data.get('website'),
            categories=data.get('categories'),
            location=data.get('location'),
            preferred_supplier=data.get('preferred_supplier', False),
            notes=data.get('notes')
        )
        db.add(new_supplier)
        db.commit()
        db.refresh(new_supplier)
        return {"success": True, "id": new_supplier.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/suppliers/{id}")
async def update_supplier(
    id: int,
    data: Dict = Body(...),
    db: Session = Depends(get_db)
):
    """Updates an existing supplier"""
    try:
        supplier = db.query(Supplier).filter(Supplier.id == id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        # Update fields
        for key, value in data.items():
            if hasattr(supplier, key):
                setattr(supplier, key, value)
        
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/suppliers/{id}")
async def delete_supplier(id: int, db: Session = Depends(get_db)):
    """Deletes a supplier"""
    try:
        db.query(Supplier).filter(Supplier.id == id).delete()
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
