from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from config.database import get_db
from database.models import ProductComparison, SupplierQuote
from typing import List, Optional, Dict
from datetime import datetime

router = APIRouter(prefix="/api/procurement/comparison", tags=["comparison"])

@router.get("/list", response_model=List[Dict])
async def get_comparisons(db: Session = Depends(get_db)):
    """Retrieves all saved comparisons"""
    try:
        comparisons = db.query(ProductComparison).order_by(ProductComparison.created_at.desc()).all()
        return [
            {
                "id": c.id,
                "title": c.title,
                "category": c.category,
                "created_at": c.created_at.isoformat(),
                "confidence_level": c.confidence_level
            } for c in comparisons
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{id}")
async def get_comparison_detail(id: int, db: Session = Depends(get_db)):
    """Retrieves full details of a specific comparison"""
    try:
        c = db.query(ProductComparison).filter(ProductComparison.id == id).first()
        if not c:
            raise HTTPException(status_code=404, detail="Comparison not found")
        
        return {
            "id": c.id,
            "title": c.title,
            "category": c.category,
            "products": c.products_json,
            "table_data": c.comparison_table_json,
            "recommendation": c.recommendation,
            "missing_info": c.missing_info_json,
            "confidence_level": c.confidence_level,
            "created_at": c.created_at.isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save")
async def save_comparison(data: Dict = Body(...), db: Session = Depends(get_db)):
    """Saves a new comparison record"""
    try:
        new_comp = ProductComparison(
            title=data.get('title'),
            category=data.get('category'),
            products_json=data.get('products'),
            comparison_table_json=data.get('table_data'),
            recommendation=data.get('recommendation'),
            missing_info_json=data.get('missing_info'),
            confidence_level=data.get('confidence_level', 'Medium')
        )
        db.add(new_comp)
        db.commit()
        db.refresh(new_comp)
        return {"success": True, "id": new_comp.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
