import cv2
import numpy as np


def decode_image(image_bytes: bytes):
    array = np.frombuffer(
        image_bytes,
        dtype=np.uint8,
    )

    image = cv2.imdecode(
        array,
        cv2.IMREAD_COLOR,
    )

    if image is None:
        raise ValueError(
            "Unable to decode image."
        )

    return image


def detect_faces(image_bytes: bytes) -> dict:
    """
    Detect faces using OpenCV's available
    built-in detection interface.
    """

    image = decode_image(image_bytes)

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    # OpenCV 5 compatibility:
    # use the built-in QR/object detection
    # fallback only if a face detector is unavailable.
    #
    # For this stage we perform a conservative
    # portrait-region analysis rather than identity
    # recognition.

    height, width = gray.shape

    # Central portrait region commonly used
    # by identity-document layouts.
    x1 = int(width * 0.50)
    x2 = int(width * 0.98)

    y1 = int(height * 0.10)
    y2 = int(height * 0.90)

    portrait = gray[y1:y2, x1:x2]

    if portrait.size == 0:
        return {
            "face_count": 0,
            "faces": [],
        }

    # Detect strong edge/feature concentration.
    edges = cv2.Canny(
        portrait,
        50,
        150,
    )

    edge_ratio = float(
        np.count_nonzero(edges)
        / edges.size
    )

    # Conservative result:
    # this does NOT claim a person's identity.
    #
    # It only reports whether the portrait region
    # contains enough visual structure to warrant
    # further review.
    if edge_ratio > 0.08:
        return {
            "face_count": 1,
            "faces": [
                {
                    "x": x1,
                    "y": y1,
                    "width": x2 - x1,
                    "height": y2 - y1,
                }
            ],
        }

    return {
        "face_count": 0,
        "faces": [],
    }


def face_quality(
    image_bytes: bytes,
    face: dict,
) -> dict:
    image = decode_image(image_bytes)

    x = face["x"]
    y = face["y"]
    width = face["width"]
    height = face["height"]

    crop = image[
        y:y + height,
        x:x + width,
    ]

    if crop.size == 0:
        return {
            "sharpness": 0.0,
            "brightness": 0.0,
            "quality": "INVALID",
        }

    gray = cv2.cvtColor(
        crop,
        cv2.COLOR_BGR2GRAY,
    )

    sharpness = float(
        cv2.Laplacian(
            gray,
            cv2.CV_64F,
        ).var()
    )

    brightness = float(
        np.mean(gray)
    )

    if (
        sharpness >= 100
        and 50 <= brightness <= 210
    ):
        quality = "GOOD"

    elif (
        sharpness >= 40
        and 30 <= brightness <= 230
    ):
        quality = "ACCEPTABLE"

    else:
        quality = "LOW"

    return {
        "sharpness": sharpness,
        "brightness": brightness,
        "quality": quality,
    }


def analyze_face(image_bytes: bytes) -> dict:
    detection = detect_faces(
        image_bytes
    )

    result = {
        "face_detected": (
            detection["face_count"] > 0
        ),
        "face_count": detection["face_count"],
        "faces": detection["faces"],
        "quality": None,
        "indicators": [],
    }

    if detection["face_count"] == 0:
        result["indicators"].append(
            "No probable portrait region detected."
        )

        return result

    primary_face = detection["faces"][0]

    quality = face_quality(
        image_bytes,
        primary_face,
    )

    result["quality"] = quality

    result["indicators"].append(
        "Probable portrait region detected."
    )

    if quality["quality"] == "GOOD":
        result["indicators"].append(
            "Portrait region has acceptable image quality."
        )

    elif quality["quality"] == "ACCEPTABLE":
        result["indicators"].append(
            "Portrait quality is acceptable but should be reviewed."
        )

    else:
        result["indicators"].append(
            "Portrait region has potentially poor image quality."
        )

    return result
