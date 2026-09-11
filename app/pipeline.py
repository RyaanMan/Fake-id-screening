from __future__ import annotations

from pathlib import Path

from app.blockchain.client import BlockchainClient
from app.blockchain.hashing import sha256_file
from app.database.db import find_document, log_action, save_screening
from app.face.engine import analyze_face
from app.forensics.copy_move import detect_copy_move
from app.forensics.ela import error_level_analysis
from app.forensics.metadata import analyze_metadata
from app.mrz.engine import analyze_mrz
from app.ocr.engine import extract_data
from app.risk.engine import calculate_risk


def analyze_document(
    image_path: str | Path,
    username: str = "demo.officer",
    role: str = "IMMIGRATION_OFFICER",
    operator_id: int | None = None,
    document_number: str = "",
) -> dict:
    image_path = Path(image_path)
    image_bytes = image_path.read_bytes()
    file_hash = sha256_file(image_path)

    # --- Forensics ------------------------------------------------------
    ela_output = image_path.with_name(image_path.stem + "_ela.png")
    ela = error_level_analysis(image_path, ela_output)
    metadata = analyze_metadata(image_path)
    copy_move = detect_copy_move(image_path)

    # --- OCR + MRZ --------------------------------------------------------
    try:
        ocr = extract_data(image_bytes)
    except Exception as exc:
        ocr = {"raw_text": "", "lines": [], "line_count": 0, "text_detected": False, "error": str(exc)}

    mrz = analyze_mrz(ocr.get("lines", []))

    # OCR confidence signal: text_detected + (if MRZ present) checksum validity.
    if ocr.get("text_detected"):
        ocr_confidence = 90.0
        if mrz.get("detected"):
            ocr_confidence = 95.0 if mrz.get("all_checks_pass") else 55.0
    else:
        ocr_confidence = 30.0

    # --- Face --------------------------------------------------------------
    try:
        face = analyze_face(image_bytes)
    except Exception as exc:
        face = {"face_detected": False, "face_count": 0, "faces": [], "quality": None, "indicators": [], "error": str(exc)}

    if face.get("face_detected"):
        quality = (face.get("quality") or {}).get("quality")
        face_match = {"GOOD": 95.0, "ACCEPTABLE": 75.0, "LOW": 50.0}.get(quality, 60.0)
    else:
        face_match = 0.0

    # --- Reference database -------------------------------------------------
    db_record = find_document(document_number) if document_number else None
    database_ok = bool(db_record and db_record.get("blacklisted") == 0 and db_record.get("status") == "ACTIVE")

    # --- Blockchain -----------------------------------------------------
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

    # --- Risk score --------------------------------------------------------
    risk = calculate_risk(
        ela_score=ela.score,
        metadata_score=metadata.score,
        copy_move_score=copy_move["score"],
        ocr_confidence=ocr_confidence,
        face_match=face_match,
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

    result = {
        "file_hash": file_hash,
        "ocr": ocr,
        "mrz": mrz,
        "face": face,
        "ela": ela.__dict__,
        "metadata": metadata.to_dict(),
        "copy_move": copy_move,
        "database": db_record,
        "blockchain": blockchain_result,
        "risk": risk,
    }

    try:
        save_screening(
            operator_id=operator_id,
            document_number=document_number,
            file_hash=file_hash,
            risk_score=risk["score"],
            risk_level=risk["level"],
            result=result,
        )
    except Exception as exc:
        result["persist_error"] = str(exc)

    return result
