"""Data models for legacy address mapping and AML requests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

Confidence = Literal["high", "medium", "low"]


@dataclass(frozen=True)
class LegacyAddress:
    """Customer legacy address row."""

    address1: str
    address2: str = ""
    town: str = ""
    county: str = ""
    postcode: str = ""


@dataclass(frozen=True)
class MappedAddress:
    """Connect identitysearch current address fields."""

    abode_no: Optional[str] = None
    building_no: Optional[str] = None
    building_name: Optional[str] = None
    street: Optional[str] = None
    sub_street: Optional[str] = None
    city: Optional[str] = None
    post_code: Optional[str] = None
    district: Optional[str] = None
    organisation: Optional[str] = None
    sub_building: Optional[str] = None

    def to_connect_dict(self) -> Dict[str, Any]:
        """Serialize to Connect ``common.person.addresses.current`` (identitysearch).

        Unrelated fields stay empty — ``subStreet`` is not copied from ``street``.
        """
        abode = self.abode_no or self.sub_building
        return {
            "abodeNo": abode or "",
            "buildingNo": self.building_no or "",
            "buildingName": self.building_name or "",
            "street": self.street or "",
            "subStreet": self.sub_street or "",
            "city": self.city or "",
            "postCode": self.post_code or "",
            "organisation": self.organisation or "",
            "subBuilding": abode or "",
            "district": self.district or "",
        }

    def to_verify_dict(self) -> Dict[str, Any]:
        """Serialize to Connect Verify ``addresses.currentAddress``.

        Every official field is present. Mapped regex parts are filled; the rest
        stay empty (including ``addressLine``, so Verify uses components).
        """
        sub = self.abode_no or self.sub_building
        return {
            "postCode": self.post_code or "",
            "addressLine": "",
            "buildingNo": self.building_no or "",
            "buildingName": self.building_name or "",
            "subBuilding": sub or "",
            "street": self.street or "",
            "town": self.city or "",
            "county": self.district or "",
        }


@dataclass
class MappingResult:
    """Outcome of mapping a legacy address row."""

    mapped: MappedAddress
    confidence: Confidence
    parseable: bool
    warnings: List[str] = field(default_factory=list)
