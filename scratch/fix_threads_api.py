import os

file_path = r'c:\Users\22001\Desktop\procurement\Executive-RFQ-Assistant-main\api\routes\threads.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacement = """@router.get("/api/tags")
async def get_tags(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tags = db.query(Tag).all()
    return {"success": True, "data": tags}

@router.post("/api/tags")
async def create_tag(data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tag = Tag(name=data.get('name'), color=data.get('color', '#6366f1'))
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return {"success": True, "tag": {"id": tag.id, "name": tag.name, "color": tag.color}}

@router.post("/api/threads/{thread_id}/tags/{tag_id}")
async def add_tag_to_thread(thread_id: str, tag_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    thread = db.query(Thread).filter(Thread.thread_id == thread_id).first()
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not thread or not tag:
        raise HTTPException(status_code=404, detail="Thread or Tag not found")
    
    if tag not in thread.tags:
        thread.tags.append(tag)
        db.commit()
    return {"success": True}
"""

if "@router.post(\"/api/tags\")" not in content:
    content = content.replace(
"""@router.get("/api/tags")
async def get_tags(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tags = db.query(Tag).all()
    return {"success": True, "data": tags}""", replacement)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Tags logic added successfully.")
else:
    print("Tags logic already exists.")
