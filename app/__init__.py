from app.routes import router
from fastapi import FastAPI
from app.models import init_db

app = FastAPI(
    title="Investment Document Q&A",
    description="Upload investment documents and ask questions about them",
    version="1.0.0"
)
app.include_router(router)

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/health")
async def health():
    return {"status": "ok"}
