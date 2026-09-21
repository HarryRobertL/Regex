"""People's Partnership PoC — legacy address mapping and Connect AML identitysearch."""

from pp_poc.aml_request_builder import build_aml_identity_search_request
from pp_poc.legacy_mapper import map_legacy_address
from pp_poc.loqate_mapper import map_loqate_address
from pp_poc.models import LegacyAddress, MappedAddress, MappingResult

__all__ = [
    "LegacyAddress",
    "MappedAddress",
    "MappingResult",
    "build_aml_identity_search_request",
    "map_legacy_address",
    "map_loqate_address",
]
