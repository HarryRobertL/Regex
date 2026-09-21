"""Tests for AML identitysearch request builder."""

from pp_poc.aml_request_builder import build_aml_identity_search_request, strip_mapping_meta
from pp_poc.models import LegacyAddress


def test_build_aml_request_shape():
    body = build_aml_identity_search_request(
        forename="Jane",
        surname="Example",
        date_of_birth="1985-04-12",
        legacy_address=LegacyAddress(
            address1="138 Belsize Road, flat 2",
            town="LONDON",
            postcode="NW3 4BA",
        ),
    )
    current = body["common"]["person"]["addresses"]["current"]
    assert current["buildingNo"] == "138"
    assert current["street"] == "Belsize Road"
    assert current["abodeNo"] == "flat 2"
    assert body["products"] == ["AML"]
    assert body["idAml"]["isAMLMultiBureau"] is True
    assert body["consumer"]["noOfAddresses"] == "2"
    assert body["common"]["person"]["dateOfBirth"] == "1985-04-12T00:00:00Z"
    assert body["_mappingMeta"]["confidence"] in ("high", "medium", "low")


def test_strip_mapping_meta_removes_poc_fields():
    body = build_aml_identity_search_request(
        forename="A",
        surname="B",
        date_of_birth="1991-04-05",
        legacy_address={"address1": "63 Tarvin Road", "town": "Chester", "postcode": "CH1 1AA"},
    )
    clean = strip_mapping_meta(body)
    assert "_mappingMeta" not in clean
