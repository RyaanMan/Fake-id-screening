from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: str | Path) -> str:
    """Return SHA-256 hex digest of a file."""
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(file_path)

    digest = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_record_hash(document_number: str, issuer: str, expiry: int) -> str:
    """Hash a small canonical record representation."""
    payload = f"{document_number}|{issuer}|{expiry}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
