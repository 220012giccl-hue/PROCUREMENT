from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..database.models import Vendor
from typing import List

router = APIRouter(tags=["Vendors"])

@router.get("")
def list_vendors(db: Session = Depends(get_db)):
    return db.query(Vendor).all()

@router.post("/")
def create_vendor(vendor_data: dict, db: Session = Depends(get_db)):
    new_vendor = Vendor(**vendor_data)
    db.add(new_vendor)
    db.commit()
    db.refresh(new_vendor)
    return new_vendor

@router.get("/{vendor_email}")
def get_vendor(vendor_email: str, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.email == vendor_email).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor

@router.put("/{vendor_email}")
def update_vendor(vendor_email: str, vendor_data: dict, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.email == vendor_email).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    for key, value in vendor_data.items():
        setattr(vendor, key, value)
    
    db.commit()
    db.refresh(vendor)
    return vendor

@router.delete("/{vendor_email}")
def delete_vendor(vendor_email: str, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.email == vendor_email).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    db.delete(vendor)
    db.commit()
    return {"status": "deleted"}
