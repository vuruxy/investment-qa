from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models import get_db
from app.services.pdf_processor import extract_text_from_pdf, chunk_text
import uuid

router = APIRouter()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    file_bytes = await file.read()
    
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    
    text = extract_text_from_pdf(file_bytes)
    
    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from this PDF. It may be corrupted or image-based")
    
    chunks = chunk_text(text)
    session_id = str(uuid.uuid4())
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute(
        "INSERT INTO documents (filename, session_id) VALUES (%s, %s) RETURNING id",
        (file.filename, session_id)
    )
    document_id = cur.fetchone()[0]
    
    for i, chunk in enumerate(chunks):
        cur.execute(
            "INSERT INTO chunks (document_id, content, chunk_index) VALUES (%s, %s, %s)",
            (document_id, chunk, i)
        )
    
    conn.commit()
    cur.close()
    conn.close()
    
    return {
        "session_id": session_id,
        "filename": file.filename,
        "chunks_created": len(chunks)
    }
