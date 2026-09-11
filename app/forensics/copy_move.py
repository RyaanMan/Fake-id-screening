from __future__ import annotations

from pathlib import Path
import cv2


def detect_copy_move(image_path: str | Path) -> dict:
    """Lightweight SIFT-based duplicate-region signal for prototype use."""
    image_path = Path(image_path)
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Unable to read image: {image_path}")

    sift = cv2.SIFT_create(nfeatures=1200)
    keypoints, descriptors = sift.detectAndCompute(image, None)

    if descriptors is None or len(keypoints) < 10:
        return {
            "score": 0.0,
            "matches": 0,
            "keypoints": len(keypoints),
            "interpretation": "Insufficient keypoints for copy-move analysis",
        }

    matcher = cv2.BFMatcher(cv2.NORM_L2)
    raw_matches = matcher.knnMatch(descriptors, descriptors, k=2)

    # Self-matches have distance 0. Ignore very close self pairs.
    good = []
    for pair in raw_matches:
        if len(pair) < 2:
            continue
        m, n = pair
        if m.queryIdx == m.trainIdx:
            continue
        if m.distance < 0.70 * n.distance:
            good.append(m)

    score = min(len(good) / max(len(keypoints), 1) * 300.0, 100.0)

    if score >= 50:
        interpretation = "Strong duplicate-region signal"
    elif score >= 20:
        interpretation = "Possible duplicate-region signal"
    else:
        interpretation = "Low duplicate-region signal"

    return {
        "score": round(score, 2),
        "matches": len(good),
        "keypoints": len(keypoints),
        "interpretation": interpretation,
    }
