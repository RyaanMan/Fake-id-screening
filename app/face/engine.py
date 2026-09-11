from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

MODEL_DIR = Path(__file__).resolve().parent / "models"
PROTOTXT = MODEL_DIR / "deploy.prototxt"
CAFFEMODEL = MODEL_DIR / "res10_300x300_ssd_iter_140000_fp16.caffemodel"

_net = None


def _load_net():
    global _net
    if _net is None:
        if not PROTOTXT.exists() or not CAFFEMODEL.exists():
            raise FileNotFoundError(
                "Face detector model files are missing from app/face/models/. "
                "Expected deploy.prototxt and res10_300x300_ssd_iter_140000_fp16.caffemodel."
            )
        _net = cv2.dnn.readNetFromCaffe(str(PROTOTXT), str(CAFFEMODEL))
    return _net


def decode_image(image_bytes: bytes):
    array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Unable to decode image.")
    return image


def _run_detector(image: np.ndarray, net_size: int, confidence_threshold: float) -> list[dict]:
    height, width = image.shape[:2]
    blob = cv2.dnn.blobFromImage(
        cv2.resize(image, (net_size, net_size)),
        scalefactor=1.0,
        size=(net_size, net_size),
        mean=(104.0, 177.0, 123.0),
    )
    net = _load_net()
    net.setInput(blob)
    detections = net.forward()

    faces = []
    for i in range(detections.shape[2]):
        confidence = float(detections[0, 0, i, 2])
        if confidence < confidence_threshold:
            continue

        box = detections[0, 0, i, 3:7] * np.array([width, height, width, height])
        x1, y1, x2, y2 = box.astype(int)
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(width, x2), min(height, y2)
        if x2 <= x1 or y2 <= y1:
            continue

        faces.append(
            {
                "x": int(x1),
                "y": int(y1),
                "width": int(x2 - x1),
                "height": int(y2 - y1),
                "confidence": round(confidence, 4),
            }
        )

    return faces


def detect_faces(image_bytes: bytes, confidence_threshold: float = 0.6) -> dict:
    """
    Real face detection using OpenCV's pretrained SSD/ResNet-10 DNN model
    (Caffe weights from the official OpenCV face-detector sample).

    ID-document photos are often a small region of a large scanned page, and
    this model's accuracy drops sharply once a small face gets crushed down
    to a fixed 300x300 input. To handle both regular photos and large scanned
    documents, we progressively retry at higher input resolutions until a
    confident detection is found.
    """

    image = decode_image(image_bytes)

    best_faces: list[dict] = []
    for net_size in (300, 500, 700, 900):
        faces = _run_detector(image, net_size, confidence_threshold)
        if faces:
            best_faces = faces
            break

    best_faces.sort(key=lambda f: f["confidence"], reverse=True)
    return {"face_count": len(best_faces), "faces": best_faces}


def face_quality(image_bytes: bytes, face: dict) -> dict:
    image = decode_image(image_bytes)

    x, y = face["x"], face["y"]
    width, height = face["width"], face["height"]

    crop = image[y : y + height, x : x + width]

    if crop.size == 0:
        return {"sharpness": 0.0, "brightness": 0.0, "quality": "INVALID"}

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(np.mean(gray))

    if sharpness >= 100 and 50 <= brightness <= 210:
        quality = "GOOD"
    elif sharpness >= 40 and 30 <= brightness <= 230:
        quality = "ACCEPTABLE"
    else:
        quality = "LOW"

    return {"sharpness": sharpness, "brightness": brightness, "quality": quality}


def compare_faces(image_bytes_a: bytes, image_bytes_b: bytes) -> dict:
    """
    Lightweight face-similarity score between two detected face crops using
    normalized cross-correlation on a resized grayscale patch. This is a
    simple, dependency-free similarity signal (not identity-grade
    recognition) intended as a decision-support input to the risk engine.
    """

    def _face_patch(image_bytes: bytes):
        detection = detect_faces(image_bytes)
        if detection["face_count"] == 0:
            return None
        f = detection["faces"][0]
        image = decode_image(image_bytes)
        crop = image[f["y"] : f["y"] + f["height"], f["x"] : f["x"] + f["width"]]
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        return cv2.resize(gray, (128, 128))

    patch_a = _face_patch(image_bytes_a)
    patch_b = _face_patch(image_bytes_b)

    if patch_a is None or patch_b is None:
        return {"comparable": False, "similarity": 0.0}

    result = cv2.matchTemplate(patch_a, patch_b, cv2.TM_CCOEFF_NORMED)
    similarity = float(np.clip(result[0][0], -1.0, 1.0))
    similarity_pct = round(((similarity + 1) / 2) * 100, 1)

    return {"comparable": True, "similarity": similarity_pct}


def analyze_face(image_bytes: bytes) -> dict:
    detection = detect_faces(image_bytes)

    result = {
        "face_detected": detection["face_count"] > 0,
        "face_count": detection["face_count"],
        "faces": detection["faces"],
        "quality": None,
        "indicators": [],
    }

    if detection["face_count"] == 0:
        result["indicators"].append("No face detected by the pretrained DNN detector.")
        return result

    primary_face = detection["faces"][0]
    quality = face_quality(image_bytes, primary_face)
    result["quality"] = quality

    result["indicators"].append(
        f"Face detected with {primary_face['confidence'] * 100:.1f}% confidence."
    )

    if quality["quality"] == "GOOD":
        result["indicators"].append("Face region has good image quality.")
    elif quality["quality"] == "ACCEPTABLE":
        result["indicators"].append("Face quality is acceptable but should be reviewed.")
    else:
        result["indicators"].append("Face region has potentially poor image quality.")

    return result
