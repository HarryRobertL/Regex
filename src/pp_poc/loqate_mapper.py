"""Map a Loqate capture response onto Connect identitysearch ``current`` fields."""

from __future__ import annotations

import re
from typing import Any, Dict, Literal, Optional

from pp_poc.models import Confidence, MappedAddress, MappingResult

AbodeMode = Literal["empty", "mirror", "number"]

_FLAT_NUMBER_RE = re.compile(
    r"(?:flat|apt|apartment|unit|suite|room|rm|studio)\s+([a-z0-9\-/]+)",
    re.IGNORECASE,
)


def _pick(payload: Dict[str, Any], *keys: str) -> str:
    lower = {str(k).strip().lower(): v for k, v in payload.items()}
    for key in keys:
        val = lower.get(key.lower())
        if val is not None and str(val).strip():
            return str(val).strip()
    return ""


def _blank(value: str) -> Optional[str]:
    s = (value or "").strip()
    return s if s else None


def extract_abode_number(sub_building: str) -> str:
    """``Flat 8`` → ``8``; otherwise the original string if it is already a number."""
    text = (sub_building or "").strip()
    if not text:
        return ""
    match = _FLAT_NUMBER_RE.search(text)
    if match:
        return match.group(1)
    if re.fullmatch(r"[a-z0-9\-/]+", text, re.IGNORECASE):
        return text
    return ""


def map_loqate_address(
    payload: Dict[str, Any],
    *,
    abode_mode: AbodeMode = "empty",
) -> MappingResult:
    """
    Map Loqate fields to Connect identitysearch ``addresses.current``.

    ``abode_mode``:
      - ``empty`` — leave ``abodeNo`` blank (safest until ops AML confirms)
      - ``mirror`` — copy Loqate ``SubBuilding`` into ``abodeNo``
      - ``number`` — ``Flat 8`` → ``abodeNo=8``
    """
    sub = _pick(payload, "SubBuilding", "subBuilding")
    building_no = _pick(payload, "BuildingNumber", "buildingNumber", "buildingNo")
    building_name = _pick(payload, "BuildingName", "buildingName")
    street = _pick(payload, "Street", "street")
    sub_street = _pick(payload, "SecondaryStreet", "secondaryStreet", "subStreet")
    city = _pick(payload, "City", "city", "Town", "town")
    district = _pick(payload, "District", "district")
    postcode = _pick(
        payload, "PostalCode", "Postcode", "PostCode", "postCode", "postcode"
    )

    if abode_mode == "mirror":
        abode = sub
    elif abode_mode == "number":
        abode = extract_abode_number(sub)
    else:
        abode = ""

    mapped = MappedAddress(
        abode_no=_blank(abode),
        building_no=_blank(building_no),
        building_name=_blank(building_name),
        street=_blank(street),
        sub_street=_blank(sub_street),
        city=_blank(city),
        post_code=_blank(postcode),
        district=_blank(district),
        organisation=_blank(_pick(payload, "Company", "organisation", "Organization")),
        sub_building=_blank(sub),
    )

    warnings: list[str] = []
    if not street and not building_name:
        warnings.append("loqate_missing_street_and_building_name")
    if not postcode:
        warnings.append("loqate_missing_postcode")
    if abode_mode == "number" and sub and not extract_abode_number(sub):
        warnings.append("loqate_abode_number_not_extracted")

    parseable = bool(street or building_name or sub)
    confidence: Confidence
    if street and (building_no or building_name) and not warnings:
        confidence = "high"
    elif parseable:
        confidence = "medium"
    else:
        confidence = "low"

    return MappingResult(
        mapped=mapped,
        confidence=confidence,
        parseable=parseable,
        warnings=warnings,
    )


def loqate_report(
    payload: Dict[str, Any],
    *,
    abode_mode: AbodeMode = "empty",
    case_id: Optional[str] = None,
) -> Dict[str, Any]:
    """JSON-serialisable Loqate → CS mapping for terminal demos."""
    mapping = map_loqate_address(payload, abode_mode=abode_mode)
    connect = mapping.mapped.to_connect_dict()
    # Keep abodeNo independent of subBuilding (unlike the concat regex path).
    connect["abodeNo"] = mapping.mapped.abode_no or ""
    connect["subBuilding"] = mapping.mapped.sub_building or ""
    report: Dict[str, Any] = {
        "source": "loqate",
        "abodeMode": abode_mode,
        "input": payload,
        "confidence": mapping.confidence,
        "parseable": mapping.parseable,
        "warnings": list(mapping.warnings),
        "connectCurrent": connect,
        "note": (
            "subBuilding is Loqate SubBuilding as-is. "
            "abodeNo depends on --abode-mode (empty|mirror|number). "
            "Confirm with a live AML request from ops."
        ),
    }
    if case_id:
        report["id"] = case_id
    return report
