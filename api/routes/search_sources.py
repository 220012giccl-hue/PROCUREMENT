from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from config.database import get_db
from database.models import PrioritySearchSource
from pydantic import BaseModel, ConfigDict
from datetime import datetime

router = APIRouter(prefix="/api/procurement/search-sources", tags=["Search Sources"])

class SearchSourceBase(BaseModel):
    name: str
    url: str
    priority: int = 1
    priority_for: Optional[str] = None
    is_active: bool = True

class SearchSourceCreate(SearchSourceBase):
    pass

class SearchSourceResponse(SearchSourceBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

@router.get("", response_model=List[SearchSourceResponse])
async def get_search_sources(db: Session = Depends(get_db)):
    sources = db.query(PrioritySearchSource).order_by(PrioritySearchSource.priority.desc()).all()
    return sources

@router.post("", response_model=SearchSourceResponse)
async def create_search_source(source: SearchSourceCreate, db: Session = Depends(get_db)):
    db_source = PrioritySearchSource(**source.dict())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source

@router.delete("/{source_id}")
async def delete_search_source(source_id: int, db: Session = Depends(get_db)):
    db_source = db.query(PrioritySearchSource).filter(PrioritySearchSource.id == source_id).first()
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(db_source)
    db.commit()
    return {"success": True}

@router.put("/{source_id}", response_model=SearchSourceResponse)
async def update_search_source(source_id: int, source: SearchSourceCreate, db: Session = Depends(get_db)):
    db_source = db.query(PrioritySearchSource).filter(PrioritySearchSource.id == source_id).first()
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    for key, value in source.dict().items():
        setattr(db_source, key, value)
    
    db_source.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_source)
    return db_source
