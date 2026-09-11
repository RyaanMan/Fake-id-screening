from __future__ import annotations


def calculate_risk(
    ela_score: float = 0.0,
    metadata_score: float = 0.0,
    copy_move_score: float = 0.0,
    ocr_confidence: float = 100.0,
    face_match: float = 100.0,
    database_ok: bool = True,
    blockchain_match: bool = True,
) -> dict:
    """Transparent hackathon rule engine. Scores are decision support, not proof."""
    score = 0.0
    reasons: list[str] = []

    score += min(max(ela_score, 0), 100) * 0.15
    score += min(max(metadata_score, 0), 100) * 0.10
    score += min(max(copy_move_score, 0), 100) * 0.15

    ocr_penalty = max(0.0, 100.0 - ocr_confidence)
    score += min(ocr_penalty, 100) * 0.10

    face_penalty = max(0.0, 100.0 - face_match)
    score += min(face_penalty, 100) * 0.20

    if not database_ok:
        score += 15
        reasons.append("Reference database mismatch / unavailable record")

    if not blockchain_match:
        score += 25
        reasons.append("Blockchain document fingerprint mismatch or unregistered")

    if ela_score >= 50:
        reasons.append("Significant ELA anomaly")
    if metadata_score >= 50:
        reasons.append("Suspicious metadata evidence")
    if copy_move_score >= 50:
        reasons.append("Possible duplicated/copy-move region")
    if ocr_confidence < 70:
        reasons.append("Low OCR confidence")
    if face_match < 70:
        reasons.append("Low face-match similarity")

    score = round(min(score, 100), 1)

    if score >= 60:
        level = "HIGH"
        action = "SEND TO HUMAN REVIEW"
    elif score >= 30:
        level = "MEDIUM"
        action = "SECONDARY CHECK"
    else:
        level = "LOW"
        action = "CLEAR / CONTINUE NORMAL CHECK"

    return {
        "score": score,
        "level": level,
        "action": action,
        "reasons": reasons or ["No high-risk rule triggered"],
    }
