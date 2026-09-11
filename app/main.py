from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.dependencies import get_current_user, require_roles
from app.auth.security import create_access_token, hash_password, verify_password
from app.config import settings
from app.database.db import (
    create_user,
    find_document,
    get_user_by_username,
    init_db,
    recent_audit,
    recent_screenings,
    seed_demo_data,
    seed_demo_users,
)
from app.pipeline import analyze_document

UPLOAD_DIR = settings.UPLOAD_DIR

init_db()
seed_demo_data()
seed_demo_users()

app = FastAPI(
    title="AI-Based Fake Identity & Document Screening System",
    version="0.2.0",
)

ROLES = {"IMMIGRATION_OFFICER", "SUPERVISOR", "AUDITOR", "ADMIN"}


@app.get("/")
def root() -> dict:
    return {"service": "Fake ID Screening API", "status": "running"}


@app.get("/health")
def health() -> dict:
    return {"status": "healthy"}


# --- Auth --------------------------------------------------------------


@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()) -> dict:
    user = get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = create_access_token(subject=user.username, role=user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username,
    }


@app.post("/auth/register")
def register(
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    full_name: str = Form(""),
    current_user: dict = Depends(require_roles("ADMIN")),
) -> dict:
    if role not in ROLES:
        raise HTTPException(status_code=400, detail=f"role must be one of {sorted(ROLES)}")
    if get_user_by_username(username):
        raise HTTPException(status_code=409, detail="Username already exists")

    user = create_user(username, hash_password(password), role, full_name or None)
    return {"username": user.username, "role": user.role, "full_name": user.full_name}


@app.get("/auth/me")
def me(current_user: dict = Depends(get_current_user)) -> dict:
    return current_user


# --- Screening -------------------------------------------------------------


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    document_number: str = Form(""),
    current_user: dict = Depends(require_roles("IMMIGRATION_OFFICER", "SUPERVISOR", "ADMIN")),
) -> dict:
    suffix = Path(file.filename or "upload.jpg").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(status_code=400, detail="Unsupported image type")

    import uuid

    target = UPLOAD_DIR / f"{Path(file.filename or 'upload').stem}_{uuid.uuid4().hex[:8]}{suffix}"
    target.write_bytes(await file.read())

    user = get_user_by_username(current_user["username"])
    return analyze_document(
        target,
        username=current_user["username"],
        role=current_user["role"],
        operator_id=user.id if user else None,
        document_number=document_number,
    )


@app.get("/documents/{document_number}")
def get_document(
    document_number: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    record = find_document(document_number)
    if not record:
        raise HTTPException(status_code=404, detail="No matching reference record")
    return record


@app.get("/screenings")
def list_screenings(
    limit: int = 100,
    current_user: dict = Depends(require_roles("SUPERVISOR", "AUDITOR", "ADMIN")),
) -> list[dict]:
    return recent_screenings(limit)


@app.get("/audit")
def audit_log(
    limit: int = 100,
    current_user: dict = Depends(require_roles("SUPERVISOR", "AUDITOR", "ADMIN")),
) -> list[dict]:
    return recent_audit(limit)
