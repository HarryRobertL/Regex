"""Thin Connect client for authenticate + AML identitysearch."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests

DEFAULT_CONNECT_BASE_URL = "https://connect.sandbox.creditsafe.com"
IDENTITY_SEARCH_PATH = "/v1/localSolutions/GB/identitysearch"
AUTH_PATH = "/v1/authenticate"


class ConnectClientError(Exception):
    """Connect API call failed."""


class ConnectClient:
    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        self.base_url = (
            base_url or os.getenv("CONNECT_BASE_URL") or DEFAULT_CONNECT_BASE_URL
        ).rstrip("/")
        self.timeout = timeout

    def authenticate(self, username: str, password: str) -> str:
        url = f"{self.base_url}{AUTH_PATH}"
        response = requests.post(
            url,
            json={"username": username, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=self.timeout,
        )
        if response.status_code != 200:
            raise ConnectClientError(
                f"Authenticate failed ({response.status_code}): {response.text}"
            )
        token = response.json().get("token")
        if not token:
            raise ConnectClientError("Authenticate response missing token")
        return token

    def run_aml_identity_search(self, token: str, body: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{IDENTITY_SEARCH_PATH}"
        payload = dict(body)
        payload.pop("_mappingMeta", None)
        response = requests.post(
            url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            timeout=self.timeout,
        )
        if response.status_code != 200:
            raise ConnectClientError(
                f"Identitysearch failed ({response.status_code}): {response.text}"
            )
        data = response.json()
        if not isinstance(data, dict):
            raise ConnectClientError("Identitysearch response is not a JSON object")
        return data

    @staticmethod
    def extract_aml_band_text(response: Dict[str, Any]) -> Optional[str]:
        aml = response.get("amlResult")
        if isinstance(aml, dict):
            band = aml.get("bandText") or aml.get("band")
            return str(band).strip() if band else None
        return None


def client_from_env() -> ConnectClient:
    return ConnectClient()


def credentials_from_env() -> tuple[str, str]:
    username = os.getenv("USERNAME") or os.getenv("CONNECT_USERNAME") or ""
    password = os.getenv("PASSWORD") or os.getenv("CONNECT_PASSWORD") or ""
    if not username or not password:
        raise ConnectClientError(
            "Set USERNAME and PASSWORD (or CONNECT_USERNAME / CONNECT_PASSWORD)"
        )
    return username, password
