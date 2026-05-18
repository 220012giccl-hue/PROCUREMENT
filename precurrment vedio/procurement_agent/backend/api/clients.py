from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from ..database.session import get_db
from ..database import crud

router = APIRouter(tags=["Clients"])

class ClientCreate(BaseModel):
    name: str
    email: str

@router.get("")
def list_clients(db: Session = Depends(get_db)):
    return crud.get_clients(db)

@router.post("")
def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    return crud.create_client(db, name=client.name, email=client.email)

@router.get("/{client_id}/projects")
def get_client_projects(client_id: int, db: Session = Depends(get_db)):
    from ..database.models import Client, Project
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    projects = db.query(Project).filter(Project.client_id == client_id).all()
    return {"client": client, "projects": projects}
