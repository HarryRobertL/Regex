"""Preprocess legacy Address1/Address2 lines before PA 3-step normalization."""

from __future__ import annotations

import re
from typing import List, Tuple

TRAILING_COMMA_FLAT_RE = re.compile(
    r",\s*((?:flat|apt|apartment|unit|suite|room|rm|studio|block)\s+[\w\-/]+)\s*$",
    re.IGNORECASE,
)
NUMBER_COMMA_STREET_RE = re.compile(
    r"^(\d+[a-z]?),\s*(.+)$",
    re.IGNORECASE,
)


def _merge_lines(address1: str, address2: str) -> str:
    a1 = (address1 or "").strip()
    a2 = (address2 or "").strip()
    if a1 and a2:
        return f"{a1}, {a2}"
    return a1 or a2


def _unwrap_number_comma_street(text: str) -> Tuple[str, List[str]]:
    """``56, Westcroft Close`` → ``56 Westcroft Close``."""
    warnings: List[str] = []
    match = NUMBER_COMMA_STREET_RE.match(text.strip())
    if match:
        warnings.append("comma_normalised")
        return f"{match.group(1)} {match.group(2).strip()}", warnings
    return text, warnings


def _peel_trailing_flat(text: str) -> Tuple[str, str, List[str]]:
    """``138 Belsize Road, flat 2`` → street blob + flat segment."""
    warnings: List[str] = []
    match = TRAILING_COMMA_FLAT_RE.search(text)
    if not match:
        return text, "", warnings
    flat_part = match.group(1).strip()
    street_blob = text[: match.start()].strip()
    warnings.append("trailing_flat_extracted")
    return street_blob, flat_part, warnings


def preprocess_legacy_line(address1: str, address2: str = "") -> Tuple[str, str, List[str]]:
    """
    Prepare a legacy address line for ``normalize_uk_address_for_bureau``.

    Returns:
        (street_blob, pre_flat, warnings)
    """
    warnings: List[str] = []
    merged = _merge_lines(address1, address2)
    if not merged:
        return "", "", warnings

    text = " ".join(merged.split())
    text, flat_value, flat_warnings = _peel_trailing_flat(text)
    warnings.extend(flat_warnings)

    text, comma_warnings = _unwrap_number_comma_street(text)
    warnings.extend(comma_warnings)

    return text, flat_value, warnings
