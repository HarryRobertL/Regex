"""Build Connect Verify individual directReport request bodies."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Union

from pp_poc.legacy_mapper import map_legacy_address_model
from pp_poc.models import LegacyAddress, MappingResult

VERIFY_PATH = "/v1/localSolutions/GB/verify/individual/directReport"

# Connect Verify reason-for-search codes (customer must pick the agreed one).
VERIFY_REASON_CODES = (
    "AM",
    "AV",
    "BS",
    "CA",
    "DC",
    "DS",
    "EC",
    "GI",
    "QS",
    "TV",
    "GC",
    "SA",
    "IA",
)


def format_dob_for_verify(date_string: str) -> str:
    """Format to ``YYYY-MM-DD`` as required by Verify."""
    if not date_string:
        return date_string
    cleaned = date_string.strip()
    for fmt in (
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
    ):
        try:
            dt = datetime.strptime(cleaned[:19].replace("Z", ""), fmt.replace("Z", ""))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(cleaned.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except ValueError:
        return cleaned[:10] if len(cleaned) >= 10 else cleaned


def build_verify_direct_report_request(
    first_name: str,
    last_name: str,
    date_of_birth: str,
    legacy_address: Union[LegacyAddress, dict],
    *,
    mapping: Optional[MappingResult] = None,
    reason_for_search: str = "AM",
    title: Optional[str] = None,
    middle_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build ``POST /v1/localSolutions/GB/verify/individual/directReport`` body.

    Sends component address fields from the PA regex (not ``addressLine``).
    """
    mapping = mapping or map_legacy_address_model(legacy_address)
    current = mapping.mapped.to_verify_dict()
    reason = (reason_for_search or "").strip().upper()
    if reason and reason not in VERIFY_REASON_CODES:
        reason = ""

    return {
        "title": (title or "").strip(),
        "firstName": (first_name or "").strip(),
        "middleName": (middle_name or "").strip(),
        "lastName": (last_name or "").strip(),
        "dateOfBirth": format_dob_for_verify(date_of_birth) if (date_of_birth or "").strip() else "",
        "reasonForSearch": reason,
        "addresses": {
            "currentAddress": current,
            "previousAddresses": [],
        },
        "_mappingMeta": {
            "confidence": mapping.confidence,
            "parseable": mapping.parseable,
            "warnings": list(mapping.warnings),
            "endpoint": VERIFY_PATH,
            "postCodeRequired": bool((current.get("postCode") or "").strip()),
        },
    }
