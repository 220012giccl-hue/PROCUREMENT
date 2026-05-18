from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..database.models import VendorDraft
from ..services.llm_client import LLMClient
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(tags=["AI Agent"])
llm_client = LLMClient()

class AnalysisRequest(BaseModel):
    email_body: str
    email_id: Optional[int] = None

class ImproveRequest(BaseModel):
    draft_id: int
    instructions: str

class ChatRequest(BaseModel):
    question: str
    chat_history: List[dict] = []
    file_id: Optional[str] = None
    context: Optional[str] = None

@router.post("/analyze")
def analyze_content(req: AnalysisRequest):
    print(f"DEBUG: [Router] Analyzing email {req.email_id}")
    products = llm_client.analyze_email(req.email_body)
    return {"products": products}

@router.post("/chat")
def ai_chat(req: ChatRequest):
    from fastapi.responses import StreamingResponse
    from ..config.prompts import GENERAL_AGENT_PROMPT
    print(f"DEBUG: [Router] AI Chat (Streaming): {req.question[:50]}...")
    
    # Start with the professional Procurement Agent identity
    messages = [{"role": "system", "content": GENERAL_AGENT_PROMPT}]
    
    for msg in req.chat_history:
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    
    if req.context:
        messages.append({"role": "system", "content": f"Context: {req.context}"})
    
    messages.append({"role": "user", "content": req.question})
    
    return StreamingResponse(llm_client.stream_chat(messages), media_type="text/plain")

@router.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    from ..services.file_processor import FileProcessor
    processor = FileProcessor()
    print(f"DEBUG: [Router] Uploading file: {file.filename}")
    
    file_path = await processor.save_file(file)
    content = processor.extract_content(file_path)
    
    return {
        "file_id": file.filename,
        "filename": file.filename,
        "content_preview": content[:200] if content else "",
        "status": "success"
    }

@router.post("/improve-draft")
def improve_draft(req: ImproveRequest, db: Session = Depends(get_db)):
    draft = db.query(VendorDraft).filter(VendorDraft.id == req.draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    improved_body = llm_client.improve_draft(draft.body, req.instructions)
    if not improved_body:
        raise HTTPException(status_code=500, detail="AI failed to improve draft")
        
    return {"improved_body": improved_body}

@router.post("/generate-drafts")
def generate_drafts(req: dict):
    # Implementation for multiple drafts generation
    return {"status": "success", "drafts": []}
