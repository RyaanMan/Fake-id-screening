from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from pathlib import Path

from app.database.db import init_db, seed_demo_data
from app.pipeline import analyze_document

BASE_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

init_db()
seed_demo_data()

app = FastAPI(
    title="AI-Based Fake Identity & Document Screening System",
    version="0.1.0",
)


@app.get("/")
def root() -> dict:
    return {
        "service": "Fake ID Screening API",
        "status": "running",
        "prototype": True,
    }


@app.get("/health")
def health() -> dict:
    return {"status": "healthy"}


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    document_number: str = Form(""),
    username: str = Form("demo.officer"),
    role: str = Form("IMMIGRATION_OFFICER"),
) -> dict:
    suffix = Path(file.filename or "upload.jpg").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(status_code=400, detail="Unsupported image type")

    target = UPLOAD_DIR / f"{Path(file.filename or 'upload').stem}_{Path().cwd().stat().st_ino}{suffix}"
    target.write_bytes(await file.read())
    return analyze_document(target, username=username, role=role, document_number=document_number)
