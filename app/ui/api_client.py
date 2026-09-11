from __future__ import annotations

import os

import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


class ApiError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"{status_code}: {detail}")


def _raise_for_status(response: requests.Response) -> None:
    if not response.ok:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise ApiError(response.status_code, detail)


def login(username: str, password: str) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        data={"username": username, "password": password},
        timeout=15,
    )
    _raise_for_status(response)
    return response.json()


def analyze_document(token: str, file_name: str, file_bytes: bytes, document_number: str = "") -> dict:
    response = requests.post(
        f"{API_BASE_URL}/analyze",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (file_name, file_bytes)},
        data={"document_number": document_number},
        timeout=120,
    )
    _raise_for_status(response)
    return response.json()


def get_document(token: str, document_number: str) -> dict | None:
    response = requests.get(
        f"{API_BASE_URL}/documents/{document_number}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    if response.status_code == 404:
        return None
    _raise_for_status(response)
    return response.json()


def list_screenings(token: str, limit: int = 100) -> list[dict]:
    response = requests.get(
        f"{API_BASE_URL}/screenings",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": limit},
        timeout=15,
    )
    _raise_for_status(response)
    return response.json()


def audit_log(token: str, limit: int = 100) -> list[dict]:
    response = requests.get(
        f"{API_BASE_URL}/audit",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": limit},
        timeout=15,
    )
    _raise_for_status(response)
    return response.json()


def register_user(token: str, username: str, password: str, role: str, full_name: str = "") -> dict:
    response = requests.post(
        f"{API_BASE_URL}/auth/register",
        headers={"Authorization": f"Bearer {token}"},
        data={"username": username, "password": password, "role": role, "full_name": full_name},
        timeout=15,
    )
    _raise_for_status(response)
    return response.json()
