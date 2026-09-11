from __future__ import annotations

from pathlib import Path

from app.blockchain.client import BlockchainClient
from app.blockchain.hashing import sha256_file
from app.database.db import find_document, log_action
from app.forensics.copy_move import detect_copy_move
from app.forensics.ela import error_level_analysis
from app.forensics.metadata import analyze_metadata
from app.risk.engine import calculate_risk


def analyze_document(
    image_path: str | Path,
    username: str = "demo.officer",
    role: str = "IMMIGRATION_OFFICER",
    document_number: str = "",
) -> dict:
    image_path = Path(image_path)
    file_hash = sha256_file(image_path)

    ela_output = image_path.with_name(image_path.stem + "_ela.png")
    ela = error_level_analysis(image_path, ela_output)
    metadata = analyze_metadata(image_path)
    copy_move = detect_copy_move(image_path)

    db_record = find_document(document_number) if document_number else None
    database_ok = bool(db_record and db_record.get("blacklisted") == 0 and db_record.get("status") == "ACTIVE")

    blockchain_result: dict = {
        "connected": False,
        "exists": False,
        "match": False,
        "issuer": None,
        "issued_at": 0,
        "expiry": 0,
        "active": False,
        "error": None,
    }

    try:
        client = BlockchainClient()
        blockchain_result = {"connected": True, **client.verify_document(file_hash)}
    except Exception as exc:
        blockchain_result["error"] = str(exc)

    # OCR and face are intentionally neutral until those modules are installed/connected.
    risk = calculate_risk(
        ela_score=ela.score,
        metadata_score=metadata.score,
        copy_move_score=copy_move["score"],
        ocr_confidence=100.0,
        face_match=100.0,
        database_ok=database_ok,
        blockchain_match=blockchain_result.get("match", False),
    )

    log_action(
        username=username,
        role=role,
        action="DOCUMENT_SCREENED",
        document_hash=file_hash,
        risk_level=risk["level"],
    )

    return {
        "file_hash": file_hash,
        "ela": ela.__dict__,
        "metadata": metadata.to_dict(),
        "copy_move": copy_move,
        "database": db_record,
        "blockchain": blockchain_result,
        "risk": risk,
    }
