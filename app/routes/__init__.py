from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from app.models import get_db
from app.services.pdf_processor import extract_text_from_pdf, chunk_text
from app.services.embeddings import embed_chunks
from app.services.rag import answer_question
import uuid

router = APIRouter()
templates = Jinja2Templates(directory="templates")

class ChatRequest(BaseModel):
    question: str
    session_id: str

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    file_bytes = await file.read()

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    text = extract_text_from_pdf(file_bytes)

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from this PDF")

    chunks = chunk_text(text)
    embeddings = embed_chunks(chunks)
    session_id = str(uuid.uuid4())

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO documents (filename, session_id) VALUES (%s, %s) RETURNING id",
            (file.filename, session_id)
        )
        document_id = cur.fetchone()[0]

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector_str = "[" + ",".join(str(x) for x in embedding) + "]"
            cur.execute(
                "INSERT INTO chunks (document_id, content, embedding, chunk_index) VALUES (%s, %s, %s::vector, %s)",
                (document_id, chunk, vector_str, i)
            )

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cur.close()
        conn.close()

    return {
        "session_id": session_id,
        "filename": file.filename,
        "chunks_created": len(chunks)
    }

@router.post("/chat")
async def chat(request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    if not request.session_id:
        raise HTTPException(status_code=400, detail="Session ID is required")

    answer = answer_question(request.question, request.session_id)

    return {
        "question": request.question,
        "answer": answer,
        "session_id": request.session_id
    }
