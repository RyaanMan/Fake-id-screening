from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from PIL import Image


@dataclass
class MetadataResult:
    has_exif: bool
    exif_count: int
    software: str | None
    make: str | None
    model: str | None
    datetime_original: str | None
    orientation: str | None
    suspicious_fields: list[str]
    score: float
    interpretation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _safe(value: Any) -> str | None:
    try:
        return None if value is None else str(value)
    except Exception:
        return None


def analyze_metadata(image_path: str | Path) -> MetadataResult:
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(image_path)
    image = Image.open(image_path)
    exif = image.getexif()

    if not exif:
        return MetadataResult(
            has_exif=False,
            exif_count=0,
            software=None,
            make=None,
            model=None,
            datetime_original=None,
            orientation=None,
            suspicious_fields=["No EXIF metadata present"],
            score=15.0,
            interpretation="No EXIF metadata — inconclusive",
        )

    software = _safe(exif.get(305))
    make = _safe(exif.get(271))
    model = _safe(exif.get(272))
    orientation = _safe(exif.get(274))
    datetime_original = _safe(exif.get(36867))

    flags: list[str] = []
    if software:
        low = software.lower()
        editing = ("photoshop", "gimp", "paint.net", "affinity", "lightroom", "snapseed", "picsart", "canva")
        if any(x in low for x in editing):
            flags.append(f"Editing software metadata detected: {software}")
    if model and not make:
        flags.append("Camera model present without manufacturer")
    if not datetime_original:
        flags.append("Original capture timestamp unavailable")

    score = 0.0
    if any("Editing software" in x for x in flags):
        score += 60.0
    if any("without manufacturer" in x for x in flags):
        score += 15.0
    if any("timestamp unavailable" in x for x in flags):
        score += 10.0
    score = min(score, 100.0)

    interpretation = "Low metadata anomaly" if score < 20 else "Moderate metadata anomaly" if score < 50 else "High metadata anomaly"
    return MetadataResult(True, len(exif), software, make, model, datetime_original, orientation, flags, round(score, 2), interpretation)
