"""UK address normalization for bureau match requests (regex / heuristics only).

Parses concat-in-street blobs into semantic fields when structured
flat / house name / house number are empty. No PAF or external lookup.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Union

STREET_SUFFIXES = (
    "road",
    "rd",
    "street",
    "st",
    "lane",
    "ln",
    "avenue",
    "ave",
    "close",
    "crescent",
    "drive",
    "dr",
    "way",
    "place",
    "pl",
    "court",
    "ct",
    "gardens",
    "grove",
    "terrace",
    "park",
    "walk",
    "hill",
    "row",
    "mews",
    "square",
    "sq",
    "rise",
    "view",
    "vale",
)

_STREET_SUFFIX_SET = frozenset(STREET_SUFFIXES)

FLAT_PREFIX_RE = re.compile(
    r"^(?:flat|apt|apartment|unit|suite|room|rm|studio|block)\s+[a-z0-9\-/]+",
    re.IGNORECASE,
)
FLAT_SUFFIX_RE = re.compile(
    r"^[a-z0-9\-/]+\s+(?:flat|apt|apartment)$",
    re.IGNORECASE,
)
HOUSE_NUMBER_RE = re.compile(
    r"^\d+[a-z]?(?:[-/]\d+[a-z]?)?$",
    re.IGNORECASE,
)
LEADING_NUMBER_RE = re.compile(
    r"^(\d+[a-z]?)(?:\s+(.+))?$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class NormalizedAddress:
    """Semantic address parts for bureau / identitysearch match requests."""

    sub_building: str = ""  # abodeNo
    building_name: str = ""  # buildingName
    building_number: str = ""  # buildingNo
    street: str = ""  # street1


def _as_text(value: Optional[Union[str, int]]) -> str:
    """Coerce optional address parts to a stripped string."""
    if value is None:
        return ""
    return str(value).strip()


def needs_normalization(
    street: Optional[str],
    flat: Optional[str] = "",
    house_name: Optional[str] = "",
    house_number: Optional[Union[str, int]] = "",
) -> bool:
    """Return True when street is present and structured fields are empty."""
    if not _as_text(street):
        return False
    if _as_text(flat) or _as_text(house_name) or _as_text(house_number):
        return False
    return True


def is_flat(value: str) -> bool:
    """True when value matches a flat / apartment / unit token pattern."""
    text = value.strip()
    if not text:
        return False
    return bool(FLAT_PREFIX_RE.fullmatch(text) or FLAT_SUFFIX_RE.fullmatch(text))


def is_house_number(value: str) -> bool:
    """True when value is a standalone UK house / unit number token."""
    return bool(HOUSE_NUMBER_RE.fullmatch(value.strip()))


def is_street(value: str) -> bool:
    """True when value ends with a known UK street suffix."""
    tokens = value.strip().split()
    if len(tokens) < 2:
        return False
    return tokens[-1].lower() in _STREET_SUFFIX_SET


def is_house_name(value: str) -> bool:
    """True when value looks like a house name (not flat, number, or street)."""
    text = value.strip()
    if not text:
        return False
    return not is_flat(text) and not is_house_number(text) and not is_street(text)


def _peel_street_from_right(text: str) -> tuple[str, str]:
    """Peel ``Name Suffix`` from the right; return (remainder, street)."""
    tokens = text.split()
    if len(tokens) < 2:
        return text, ""
    if tokens[-1].lower() not in _STREET_SUFFIX_SET:
        return text, ""
    street_out = f"{tokens[-2]} {tokens[-1]}"
    remainder = " ".join(tokens[:-2]).strip()
    return remainder, street_out


def _peel_flat_from_left(remainder: str) -> tuple[str, str]:
    """Peel flat prefix/suffix from remainder; return (sub_building, leftover)."""
    if not remainder:
        return "", ""
    match = FLAT_PREFIX_RE.match(remainder)
    if match:
        sub = match.group(0).strip()
        leftover = remainder[match.end() :].strip()
        return sub, leftover
    match = FLAT_SUFFIX_RE.match(remainder)
    if match:
        sub = match.group(0).strip()
        leftover = remainder[match.end() :].strip()
        return sub, leftover
    if is_flat(remainder):
        return remainder.strip(), ""
    return "", remainder


def _score_remainder(remainder: str, sub_building: str) -> tuple[str, str, str]:
    """Assign building_name / building_number / optional abode from leftover tokens."""
    if not remainder:
        return "", "", sub_building

    tokens = remainder.split()
    number_idx: Optional[int] = None
    for i in range(len(tokens) - 1, -1, -1):
        if is_house_number(tokens[i]):
            number_idx = i
            break

    if number_idx is not None:
        building_number = tokens[number_idx]
        before_tokens = tokens[:number_idx]
        sub = sub_building
        if before_tokens and not sub and is_house_number(before_tokens[-1]):
            sub = before_tokens[-1]
            before_tokens = before_tokens[:-1]
        building_name = " ".join(before_tokens).strip()
        return building_name, building_number, sub

    lead = LEADING_NUMBER_RE.match(remainder)
    if lead:
        return (lead.group(2) or "").strip(), lead.group(1), sub_building

    return remainder, "", sub_building


def normalize_uk_address_for_bureau(
    street: Optional[str] = "",
    flat: Optional[str] = "",
    house_name: Optional[str] = "",
    house_number: Optional[Union[str, int]] = "",
) -> NormalizedAddress:
    """Normalize a UK address blob into semantic bureau fields.

    When structured fields are already present, returns them unchanged.
    Otherwise peels street suffix (right), flat (left), then scores remainder.
    """
    street_in = _as_text(street)
    flat_in = _as_text(flat)
    house_name_in = _as_text(house_name)
    house_number_in = _as_text(house_number)

    if not needs_normalization(street_in, flat_in, house_name_in, house_number_in):
        return NormalizedAddress(
            sub_building=flat_in,
            building_name=house_name_in,
            building_number=house_number_in,
            street=street_in,
        )

    text = " ".join(street_in.split())
    remainder, street_out = _peel_street_from_right(text)
    sub_building, remainder = _peel_flat_from_left(remainder)
    building_name, building_number, sub_building = _score_remainder(
        remainder, sub_building
    )

    if not street_out and sub_building and not building_name and not building_number:
        return NormalizedAddress(
            sub_building=sub_building,
            building_name="",
            building_number="",
            street="",
        )

    return NormalizedAddress(
        sub_building=sub_building,
        building_name=building_name,
        building_number=building_number,
        street=street_out or text,
    )
