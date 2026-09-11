from pathlib import Path

import cv2
import numpy as np
import pytesseract


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    Convert uploaded image bytes into a cleaned image
    suitable for OCR.
    """

    image_array = np.frombuffer(
        image_bytes,
        dtype=np.uint8,
    )

    image = cv2.imdecode(
        image_array,
        cv2.IMREAD_COLOR,
    )

    if image is None:
        raise ValueError("Unable to decode uploaded image.")

    # Convert to grayscale
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    # Upscale small documents
    gray = cv2.resize(
        gray,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC,
    )

    # Reduce noise
    gray = cv2.GaussianBlur(
        gray,
        (3, 3),
        0,
    )

    # Improve contrast
    processed = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )[1]

    return processed


def extract_text(image_bytes: bytes) -> str:
    """
    Run Tesseract OCR against the uploaded image.
    """

    processed = preprocess_image(image_bytes)

    text = pytesseract.image_to_string(
        processed,
        config="--psm 6",
    )

    return text.strip()


def extract_data(image_bytes: bytes) -> dict:
    """
    Return structured OCR information for the screening system.
    """

    text = extract_text(image_bytes)

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    return {
        "raw_text": text,
        "lines": lines,
        "line_count": len(lines),
        "text_detected": bool(text),
    }
