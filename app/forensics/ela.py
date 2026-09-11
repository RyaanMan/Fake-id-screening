from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


@dataclass
class ELAResult:
    score: float
    mean_error: float
    max_error: float
    high_error_ratio: float
    output_path: str
    interpretation: str


def error_level_analysis(
    image_path: str | Path,
    output_path: str | Path,
    quality: int = 90,
    threshold_percentile: float = 95.0,
) -> ELAResult:
    """Generate a JPEG recompression difference map; evidence only, not proof."""
    image_path = Path(image_path)
    output_path = Path(output_path)
    if not image_path.exists():
        raise FileNotFoundError(image_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    original = Image.open(image_path).convert("RGB")
    temp_path = output_path.parent / "_ela_recompressed.jpg"
    original.save(temp_path, "JPEG", quality=quality)
    recompressed = Image.open(temp_path).convert("RGB")

    a = np.asarray(original, dtype=np.int16)
    b = np.asarray(recompressed, dtype=np.int16)
    error_map = np.max(np.abs(a - b), axis=2).astype(np.float32)

    mean_error = float(error_map.mean())
    max_error = float(error_map.max())
    threshold = float(np.percentile(error_map, threshold_percentile))
    high_error_ratio = float((error_map >= threshold).mean() * 100.0)

    if max_error:
        visual = np.clip(error_map * (255.0 / max_error), 0, 255).astype(np.uint8)
    else:
        visual = np.zeros_like(error_map, dtype=np.uint8)
    visual = cv2.GaussianBlur(visual, (3, 3), 0)
    cv2.imwrite(str(output_path), visual)
    temp_path.unlink(missing_ok=True)

    score = min(100.0, 0.50 * min(mean_error * 5.0, 100.0)
                + 0.20 * min(max_error * 1.5, 100.0)
                + 0.30 * min(high_error_ratio * 2.0, 100.0))
    if score < 20:
        interpretation = "Low recompression anomaly"
    elif score < 50:
        interpretation = "Moderate recompression anomaly"
    else:
        interpretation = "High recompression anomaly"

    return ELAResult(
        score=round(score, 2),
        mean_error=round(mean_error, 2),
        max_error=round(max_error, 2),
        high_error_ratio=round(high_error_ratio, 2),
        output_path=str(output_path),
        interpretation=interpretation,
    )
