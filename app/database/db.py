from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any, Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.database.models import AuditLog, Base, ReferenceDocument, Screening, User

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def seed_demo_data() -> None:
    rows = [
        ("DEMO123456", "TEST PERSON", "IND", "2030-01-01", "ACTIVE", False),
        ("BLOCK000001", "BLACKLIST DEMO", "IND", "2028-01-01", "BLACKLISTED", True),
        ("EXPIRE00001", "EXPIRED DEMO", "IND", "2020-01-01", "EXPIRED", False),
    ]
    with get_session() as session:
        for document_number, name, nationality, expiry, status, blacklisted in rows:
            existing = session.get(ReferenceDocument, document_number)
            if existing:
                continue
            session.add(
                ReferenceDocument(
                    document_number=document_number,
                    name=name,
                    nationality=nationality,
                    expiry=expiry,
                    status=status,
                    blacklisted=blacklisted,
                )
            )


def find_document(document_number: str) -> dict[str, Any] | None:
    if not document_number:
        return None
    with get_session() as session:
        row = session.get(ReferenceDocument, document_number)
        if not row:
            return None
        return {
            "document_number": row.document_number,
            "name": row.name,
            "nationality": row.nationality,
            "expiry": row.expiry,
            "status": row.status,
            "blacklisted": int(row.blacklisted),
        }


def log_action(
    username: str,
    role: str,
    action: str,
    document_hash: str | None,
    risk_level: str | None,
) -> None:
    with get_session() as session:
        session.add(
            AuditLog(
                username=username,
                role=role,
                action=action,
                document_hash=document_hash,
                risk_level=risk_level,
            )
        )


def recent_audit(limit: int = 50) -> list[dict[str, Any]]:
    with get_session() as session:
        rows = (
            session.query(AuditLog)
            .order_by(AuditLog.id.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": row.id,
                "username": row.username,
                "role": row.role,
                "action": row.action,
                "document_hash": row.document_hash,
                "risk_level": row.risk_level,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]


def save_screening(
    operator_id: int | None,
    document_number: str | None,
    file_hash: str,
    risk_score: float,
    risk_level: str,
    result: dict[str, Any],
) -> int:
    with get_session() as session:
        record = Screening(
            operator_id=operator_id,
            document_number=document_number or None,
            file_hash=file_hash,
            risk_score=risk_score,
            risk_level=risk_level,
            result_json=json.dumps(result),
        )
        session.add(record)
        session.flush()
        return record.id


def recent_screenings(limit: int = 100) -> list[dict[str, Any]]:
    with get_session() as session:
        rows = (
            session.query(Screening)
            .order_by(Screening.id.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": row.id,
                "operator_id": row.operator_id,
                "document_number": row.document_number,
                "file_hash": row.file_hash,
                "risk_score": row.risk_score,
                "risk_level": row.risk_level,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]


def get_user_by_username(username: str) -> User | None:
    with get_session() as session:
        user = session.query(User).filter(User.username == username).first()
        if user:
            session.expunge(user)
        return user


def create_user(username: str, password_hash: str, role: str, full_name: str | None = None) -> User:
    with get_session() as session:
        user = User(username=username, password_hash=password_hash, role=role, full_name=full_name)
        session.add(user)
        session.flush()
        session.refresh(user)
        session.expunge(user)
        return user


def seed_demo_users() -> None:
    """Create a default admin/demo account set if none exist yet."""
    from app.auth.security import hash_password

    defaults = [
        ("admin", "Admin@2026", "ADMIN", "System Administrator"),
        ("demo.officer", "Officer@2026", "IMMIGRATION_OFFICER", "Demo Immigration Officer"),
        ("demo.supervisor", "Supervisor@2026", "SUPERVISOR", "Demo Supervisor"),
        ("demo.auditor", "Auditor@2026", "AUDITOR", "Demo Auditor"),
    ]
    for username, password, role, full_name in defaults:
        if get_user_by_username(username):
            continue
        create_user(username, hash_password(password), role, full_name)
