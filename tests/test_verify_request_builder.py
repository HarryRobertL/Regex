"""Tests for Connect Verify payload mapping."""

from pp_poc.aml_request_builder import strip_mapping_meta
from pp_poc.legacy_mapper import map_legacy_address
from pp_poc.mapping_report import mapping_report
from pp_poc.verify_request_builder import build_verify_direct_report_request


def test_verify_fields_use_subbuilding_town_not_abodeno_city():
    mapping = map_legacy_address(
        address1="138 Belsize Road, flat 2",
        town="LONDON",
        county="United Kingdom",
        postcode="NW3 4BA",
    )
    verify = mapping.mapped.to_verify_dict()
    assert verify == {
        "postCode": "NW3 4BA",
        "addressLine": "",
        "buildingNo": "138",
        "buildingName": "",
        "subBuilding": "flat 2",
        "street": "Belsize Road",
        "town": "LONDON",
        "county": "United Kingdom",
    }
    assert "abodeNo" not in verify
    assert "city" not in verify
    assert "subStreet" not in verify


def test_verify_request_shape():
    body = build_verify_direct_report_request(
        first_name="Jane",
        last_name="Example",
        date_of_birth="1985-04-12",
        legacy_address={
            "address1": "56, Westcroft Close",
            "town": "LONDON",
            "postcode": "SW1A 1AA",
        },
        reason_for_search="AM",
    )
    current = body["addresses"]["currentAddress"]
    assert current["buildingNo"] == "56"
    assert current["street"] == "Westcroft Close"
    assert current["town"] == "LONDON"
    assert current["postCode"] == "SW1A 1AA"
    assert body["dateOfBirth"] == "1985-04-12"
    assert body["reasonForSearch"] == "AM"
    assert current["addressLine"] == ""
    assert body["addresses"]["previousAddresses"] == []
    assert body["title"] == ""
    assert body["middleName"] == ""
    clean = strip_mapping_meta(body)
    assert "_mappingMeta" not in clean
    assert clean["addresses"]["currentAddress"]["buildingNo"] == "56"


def test_mapping_report_includes_verify_and_full_verify_request():
    report = mapping_report(
        address1="138 Belsize Road, flat 2",
        town="LONDON",
        postcode="NW3 4BA",
        full_request=True,
        target="verify",
    )
    assert report["verifyCurrent"]["subBuilding"] == "flat 2"
    assert report["verifyCurrent"]["town"] == "LONDON"
    assert report["request"]["addresses"]["currentAddress"]["street"] == "Belsize Road"
    assert report["request"]["firstName"] == ""
    assert report["request"]["addresses"]["currentAddress"]["addressLine"] == ""
    assert "products" not in report["request"]
