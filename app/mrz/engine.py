import re


MRZ_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<"


def normalize_line(line: str) -> str:
    """
    Normalize OCR output for MRZ processing.
    """

    line = line.upper().strip()

    # Remove spaces and characters that cannot belong to MRZ.
    line = line.replace(" ", "")

    line = "".join(
        char
        for char in line
        if char in MRZ_CHARS
    )

    return line


def char_value(char: str) -> int:
    """
    ICAO MRZ character weighting value.
    """

    if char == "<":
        return 0

    if char.isdigit():
        return int(char)

    return ord(char) - ord("A") + 10


def checksum(value: str) -> int:
    """
    Calculate ICAO 9303 MRZ check digit.
    """

    weights = [7, 3, 1]

    total = 0

    for index, char in enumerate(value):
        total += (
            char_value(char)
            * weights[index % 3]
        )

    return total % 10


def validate_check_digit(
    value: str,
    expected: str,
) -> bool:
    """
    Validate a single MRZ check digit.
    """

    if not expected.isdigit():
        return False

    return checksum(value) == int(expected)


def looks_like_mrz(line: str) -> bool:
    """
    Determine whether a line resembles an MRZ line.
    """

    line = normalize_line(line)

    if len(line) < 30:
        return False

    allowed = sum(
        char in MRZ_CHARS
        for char in line
    )

    ratio = allowed / len(line)

    return ratio >= 0.95


def find_mrz_lines(lines: list[str]) -> list[str]:
    """
    Find likely consecutive MRZ lines.
    """

    normalized = [
        normalize_line(line)
        for line in lines
    ]

    candidates = []

    for index in range(len(normalized) - 1):
        first = normalized[index]
        second = normalized[index + 1]

        if (
            looks_like_mrz(first)
            and looks_like_mrz(second)
        ):
            candidates = [
                first,
                second,
            ]

    return candidates


def parse_td3(lines: list[str]) -> dict:
    """
    Parse a two-line TD3 passport-style MRZ.

    This parser is intentionally limited to structural
    and checksum validation.
    """

    if len(lines) != 2:
        return {
            "valid": False,
            "reason": "Two MRZ lines required.",
        }

    line1, line2 = lines

    if len(line1) != 44 or len(line2) != 44:
        return {
            "valid": False,
            "reason": (
                "TD3 MRZ lines should contain "
                "44 characters each."
            ),
        }

    document_type = line1[0:2]
    issuing_state = line1[2:5]

    names = line1[5:44]

    document_number = line2[0:9]
    document_number_check = line2[9]

    nationality = line2[10:13]

    birth_date = line2[13:19]
    birth_date_check = line2[19]

    sex = line2[20]

    expiry_date = line2[21:27]
    expiry_date_check = line2[27]

    optional_data = line2[28:42]

    optional_data_check = line2[42]

    composite_data = (
        line2[0:10]
        + line2[13:20]
        + line2[21:43]
    )

    composite_check = line2[43]

    checks = {
        "document_number": validate_check_digit(
            document_number,
            document_number_check,
        ),
        "birth_date": validate_check_digit(
            birth_date,
            birth_date_check,
        ),
        "expiry_date": validate_check_digit(
            expiry_date,
            expiry_date_check,
        ),
        "optional_data": validate_check_digit(
            optional_data,
            optional_data_check,
        ),
        "composite": validate_check_digit(
            composite_data,
            composite_check,
        ),
    }

    return {
        "valid": all(checks.values()),
        "document_type": document_type,
        "issuing_state": issuing_state,
        "names_raw": names,
        "document_number": document_number,
        "nationality": nationality,
        "birth_date": birth_date,
        "sex": sex,
        "expiry_date": expiry_date,
        "check_digits": checks,
        "all_checks_pass": all(checks.values()),
    }


def analyze_mrz(ocr_lines: list[str]) -> dict:
    """
    Run complete MRZ detection and validation.
    """

    mrz_lines = find_mrz_lines(
        ocr_lines
    )

    if not mrz_lines:
        return {
            "detected": False,
            "valid": False,
            "reason": "No probable MRZ detected.",
            "lines": [],
        }

    result = parse_td3(mrz_lines)

    result["detected"] = True
    result["lines"] = mrz_lines

    return result
