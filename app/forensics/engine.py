from io import BytesIO

import cv2
import numpy as np
from PIL import Image, ExifTags


def decode_image(image_bytes: bytes):
    """
    Decode uploaded image bytes with OpenCV.
    """

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


def image_properties(image_bytes: bytes) -> dict:
    """
    Collect basic image properties.
    """

    image = decode_image(image_bytes)

    height, width = image.shape[:2]

    channels = (
        image.shape[2]
        if len(image.shape) == 3
        else 1
    )

    return {
        "width": width,
        "height": height,
        "channels": channels,
        "pixels": width * height,
    }


def extract_metadata(image_bytes: bytes) -> dict:
    """
    Extract available EXIF metadata.
    """

    metadata = {}

    try:
        image = Image.open(
            BytesIO(image_bytes)
        )

        exif = image.getexif()

        for key, value in exif.items():
            tag = ExifTags.TAGS.get(
                key,
                str(key),
            )

            metadata[tag] = str(value)

    except Exception:
        pass

    return metadata


def error_level_analysis(
    image_bytes: bytes,
    quality: int = 90,
) -> np.ndarray:
    """
    Generate an Error Level Analysis image.

    ELA is a forensic visualization technique.
    It should be treated as an indicator, not proof
    of manipulation.
    """

    original = Image.open(
        BytesIO(image_bytes)
    ).convert("RGB")

    buffer = BytesIO()

    original.save(
        buffer,
        format="JPEG",
        quality=quality,
    )

    recompressed = Image.open(
        BytesIO(buffer.getvalue())
    ).convert("RGB")

    original_array = np.asarray(
        original,
        dtype=np.int16,
    )

    recompressed_array = np.asarray(
        recompressed,
        dtype=np.int16,
    )

    difference = np.abs(
        original_array
        - recompressed_array
    )

    maximum = difference.max()

    if maximum == 0:
        maximum = 1

    ela = (
        difference
        * (255.0 / maximum)
    ).clip(
        0,
        255,
    ).astype(
        np.uint8
    )

    return ela


def ela_statistics(
    ela_image: np.ndarray,
) -> dict:
    """
    Calculate summary statistics for ELA.
    """

    gray = cv2.cvtColor(
        ela_image,
        cv2.COLOR_RGB2GRAY,
    )

    return {
        "mean": float(
            np.mean(gray)
        ),
        "maximum": int(
            np.max(gray)
        ),
        "std": float(
            np.std(gray)
        ),
    }


def analyze_forensics(
    image_bytes: bytes,
) -> dict:
    """
    Run the complete forensic inspection.
    """

    properties = image_properties(
        image_bytes
    )

    metadata = extract_metadata(
        image_bytes
    )

    ela = error_level_analysis(
        image_bytes
    )

    statistics = ela_statistics(
        ela
    )

    indicators = []

    if not metadata:
        indicators.append(
            "No EXIF metadata was available."
        )
    else:
        indicators.append(
            f"{len(metadata)} EXIF metadata fields detected."
        )

    if statistics["mean"] > 30:
        indicators.append(
            "ELA shows relatively high average pixel differences."
        )
    else:
        indicators.append(
            "ELA shows relatively low average pixel differences."
        )

    if properties["width"] < 800:
        indicators.append(
            "Image resolution is relatively low."
        )

    return {
        "properties": properties,
        "metadata": metadata,
        "ela_image": ela,
        "ela_statistics": statistics,
        "indicators": indicators,
    }
