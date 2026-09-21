"""JSON reports for terminal / customer demos of legacy → Connect mapping."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional

from pp_poc.aml_request_builder import build_aml_identity_search_request, strip_mapping_meta
from pp_poc.legacy_mapper import map_legacy_address
from pp_poc.verify_request_builder import build_verify_direct_report_request


def _pick(case: Dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        val = case.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return default


def mapping_report(
    *,
    address1: str,
    address2: str = "",
    town: str = "",
    county: str = "",
    postcode: str = "",
    case_id: Optional[str] = None,
    group: Optional[str] = None,
    note: Optional[str] = None,
    full_request: bool = False,
    forename: str = "",
    surname: str = "",
    date_of_birth: str = "",
    target: str = "verify",
    reason_for_search: str = "",
) -> Dict[str, Any]:
    """Map one legacy address and return a JSON-serialisable report."""
    mapping = map_legacy_address(
        address1=address1,
        address2=address2,
        town=town,
        county=county,
        postcode=postcode,
    )
    verify_current = mapping.mapped.to_verify_dict()
    warnings = list(mapping.warnings)
    if not (verify_current.get("postCode") or "").strip():
        warnings.append("verify_postcode_required")
    report: Dict[str, Any] = {
        "input": {
            "address1": address1,
            "address2": address2 or "",
            "town": town or "",
            "county": county or "",
            "postcode": postcode or "",
        },
        "confidence": mapping.confidence,
        "parseable": mapping.parseable,
        "warnings": warnings,
        "verifyCurrent": verify_current,
    }
    if target == "identitysearch":
        report["connectCurrent"] = mapping.mapped.to_connect_dict()
    if case_id:
        report["id"] = case_id
    if group:
        report["group"] = group
    if note:
        report["note"] = note
    if full_request:
        legacy = {
            "address1": address1,
            "address2": address2,
            "town": town,
            "county": county,
            "postcode": postcode,
        }
        if target == "identitysearch":
            body = build_aml_identity_search_request(
                forename=forename,
                surname=surname,
                date_of_birth=date_of_birth,
                legacy_address=legacy,
                mapping=mapping,
            )
            endpoint = "/v1/localSolutions/GB/identitysearch"
        else:
            body = build_verify_direct_report_request(
                first_name=forename,
                last_name=surname,
                date_of_birth=date_of_birth,
                legacy_address=legacy,
                mapping=mapping,
                reason_for_search=reason_for_search,
            )
            endpoint = "/v1/localSolutions/GB/verify/individual/directReport"
        report["endpoint"] = endpoint
        report["request"] = strip_mapping_meta(body)
    return report


def mapping_report_from_case(
    case: Dict[str, Any],
    *,
    full_request: bool = False,
    forename: str = "",
    surname: str = "",
    date_of_birth: str = "",
    target: str = "verify",
    reason_for_search: str = "",
) -> Dict[str, Any]:
    """Map a fixture/CSV-style case dict."""
    return mapping_report(
        address1=_pick(case, "address1", "Address1"),
        address2=_pick(case, "address2", "Address2"),
        town=_pick(case, "town", "Town"),
        county=_pick(case, "county", "County"),
        postcode=_pick(case, "postcode", "PostCode", "postCode"),
        case_id=_pick(case, "id") or None,
        group=_pick(case, "group") or None,
        note=_pick(case, "note") or None,
        full_request=full_request,
        forename=forename,
        surname=surname,
        date_of_birth=date_of_birth,
        target=target,
        reason_for_search=reason_for_search,
    )


def mapping_report_batch(
    cases: List[Dict[str, Any]],
    *,
    full_request: bool = False,
    forename: str = "",
    surname: str = "",
    date_of_birth: str = "",
    target: str = "verify",
    reason_for_search: str = "",
) -> Dict[str, Any]:
    """Map many cases; return summary + results for JSON stdout."""
    results = [
        mapping_report_from_case(
            case,
            full_request=full_request,
            forename=forename,
            surname=surname,
            date_of_birth=date_of_birth,
            target=target,
            reason_for_search=reason_for_search,
        )
        for case in cases
    ]
    counts: Counter[str] = Counter(r["confidence"] for r in results)
    total = len(results)
    high_medium = counts.get("high", 0) + counts.get("medium", 0)
    return {
        "summary": {
            "total": total,
            "parseable": sum(1 for r in results if r["parseable"]),
            "confidence": dict(counts),
            "high_medium_pct": round(100.0 * high_medium / total, 1) if total else 0.0,
        },
        "results": results,
    }
