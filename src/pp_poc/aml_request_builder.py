"""Build Connect AML Multi-Bureau identitysearch request bodies."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Union

from pp_poc.legacy_mapper import map_legacy_address_model
from pp_poc.models import LegacyAddress, MappingResult


def _blank_to_none(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def format_dob_for_connect(date_string: str) -> str:
    """Format ``yyyy-mm-dd`` (or common variants) to ``YYYY-MM-DDTHH:MM:SSZ``."""
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
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(cleaned.replace("Z", "+00:00")).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    except ValueError:
        return cleaned


def _empty_connect_address() -> Dict[str, Any]:
    return {
        "abodeNo": None,
        "buildingNo": None,
        "buildingName": None,
        "street": None,
        "subStreet": None,
        "city": None,
        "postCode": None,
        "organisation": None,
        "subBuilding": None,
        "district": None,
    }


def build_aml_identity_search_request(
    forename: str,
    surname: str,
    date_of_birth: str,
    legacy_address: Union[LegacyAddress, dict],
    *,
    mapping: Optional[MappingResult] = None,
) -> Dict[str, Any]:
    """
    Build full ``POST /v1/localSolutions/GB/identitysearch`` body for AML Multi-Bureau.

    Current address only; ``products`` is ``["AML"]``.
    """
    mapping = mapping or map_legacy_address_model(legacy_address)
    current = mapping.mapped.to_connect_dict()
    empty = _empty_connect_address()
    dob = format_dob_for_connect(date_of_birth)

    return {
        "common": {
            "person": {
                "currentName": {
                    "title": None,
                    "forename": _blank_to_none(forename),
                    "otherNames": None,
                    "surname": _blank_to_none(surname),
                    "suffix": None,
                },
                "previousName": {
                    "title": None,
                    "forename": None,
                    "otherNames": None,
                    "surname": None,
                    "suffix": None,
                },
                "dateOfBirth": dob,
                "gender": None,
                "addresses": {
                    "current": current,
                    "previous1": dict(empty),
                    "previous2": dict(empty),
                },
            },
            "reference": None,
        },
        "consumer": {
            "noOfAddresses": "2",
            "secondPerson": {
                "currentName": {"title": None, "otherNames": None, "suffix": None},
                "previousName": {
                    "title": None,
                    "forename": None,
                    "otherNames": None,
                    "surname": None,
                    "suffix": None,
                },
                "dateOfBirth": None,
                "gender": None,
                "addresses": {
                    "current": {
                        "abodeNo": None,
                        "buildingNo": None,
                        "buildingName": None,
                        "street": None,
                        "city": None,
                        "postCode": None,
                    },
                    "previous1": {
                        "buildingNo": None,
                        "buildingName": None,
                        "street": None,
                        "city": None,
                        "postCode": None,
                    },
                    "previous2": {
                        "buildingNo": None,
                        "buildingName": None,
                        "street": None,
                        "city": None,
                        "postCode": None,
                    },
                },
            },
            "reason": None,
            "thirdPartyOptIn": None,
        },
        "idAml": {
            "landlineNumber": None,
            "exDirectory": None,
            "sortCode": None,
            "bankAccountNumber": None,
            "isAMLMultiBureau": True,
        },
        "products": ["AML"],
        "_mappingMeta": {
            "confidence": mapping.confidence,
            "parseable": mapping.parseable,
            "warnings": list(mapping.warnings),
        },
    }


def strip_mapping_meta(body: Dict[str, Any]) -> Dict[str, Any]:
    """Remove PoC-only metadata before sending to Connect."""
    out = dict(body)
    out.pop("_mappingMeta", None)
    return out
