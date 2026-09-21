"""Map legacy Address1/Address2 rows to Connect identitysearch address fields."""

from __future__ import annotations

from typing import Optional, Union

from pp_poc.legacy_preprocess import preprocess_legacy_line
from pp_poc.models import Confidence, LegacyAddress, MappedAddress, MappingResult
from pp_poc.uk_address_normalization import (
    NormalizedAddress,
    normalize_uk_address_for_bureau,
)


def _blank_to_none(value: str) -> Optional[str]:
    s = (value or "").strip()
    return s if s else None


def _norm_to_mapped(norm: NormalizedAddress, town: str, postcode: str, county: str) -> MappedAddress:
    return MappedAddress(
        abode_no=_blank_to_none(norm.sub_building),
        building_no=_blank_to_none(norm.building_number),
        building_name=_blank_to_none(norm.building_name),
        street=_blank_to_none(norm.street),
        sub_street=None,
        city=_blank_to_none(town),
        post_code=_blank_to_none(postcode),
        district=_blank_to_none(county),
        organisation=None,
        sub_building=_blank_to_none(norm.sub_building),
    )


def _assess_confidence(norm: NormalizedAddress, warnings: list[str]) -> tuple[Confidence, bool]:
    has_street = bool((norm.street or "").strip())
    has_number_or_name = bool(
        (norm.building_number or "").strip() or (norm.building_name or "").strip()
    )
    if has_street and has_number_or_name and not warnings:
        return "high", True
    if has_street and (has_number_or_name or norm.sub_building):
        return "medium", True
    if has_street or norm.sub_building:
        return "low", True
    return "low", False


def map_legacy_address(
    address1: str,
    address2: str = "",
    town: str = "",
    county: str = "",
    postcode: str = "",
) -> MappingResult:
    """
    Map customer legacy columns to Connect current-address fields.

    Uses legacy preprocess (comma / trailing flat) then PA 3-step bureau normalizer.
    """
    warnings: list[str] = []
    street_blob, pre_flat, preprocess_warnings = preprocess_legacy_line(address1, address2)
    warnings.extend(preprocess_warnings)

    if not street_blob and not pre_flat:
        empty = MappedAddress(city=_blank_to_none(town), post_code=_blank_to_none(postcode))
        return MappingResult(
            mapped=empty,
            confidence="low",
            parseable=False,
            warnings=warnings + ["empty_address_lines"],
        )

    norm = normalize_uk_address_for_bureau(street=street_blob)
    sub_building = pre_flat or norm.sub_building
    norm = NormalizedAddress(
        sub_building=sub_building,
        building_name=norm.building_name,
        building_number=norm.building_number,
        street=norm.street,
    )
    mapped = _norm_to_mapped(norm, town, postcode, county)
    confidence, parseable = _assess_confidence(norm, warnings)

    if not (norm.street or "").strip() and not warnings:
        warnings.append("no_street_suffix_found")

    return MappingResult(
        mapped=mapped,
        confidence=confidence,
        parseable=parseable,
        warnings=warnings,
    )


def map_legacy_address_model(address: Union[LegacyAddress, dict]) -> MappingResult:
    """Convenience wrapper accepting ``LegacyAddress`` or dict."""
    if isinstance(address, dict):
        return map_legacy_address(
            address1=address.get("address1") or address.get("Address1") or "",
            address2=address.get("address2") or address.get("Address2") or "",
            town=address.get("town") or address.get("Town") or "",
            county=address.get("county") or address.get("County") or "",
            postcode=address.get("postcode") or address.get("PostCode") or "",
        )
    return map_legacy_address(
        address1=address.address1,
        address2=address.address2,
        town=address.town,
        county=address.county,
        postcode=address.postcode,
    )
