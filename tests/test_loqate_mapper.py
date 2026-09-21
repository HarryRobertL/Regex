"""Loqate capture → Connect identitysearch current address."""

from pp_poc.loqate_mapper import extract_abode_number, loqate_report, map_loqate_address

SHANKLIN = {
    "SubBuilding": "Flat 8",
    "BuildingNumber": "",
    "BuildingName": "Shanklin Towers",
    "SecondaryStreet": "",
    "Street": "Prospect Road",
    "Block": "",
    "Neighbourhood": "",
    "District": "",
    "City": "Shanklin",
}


def test_extract_abode_number():
    assert extract_abode_number("Flat 8") == "8"
    assert extract_abode_number("Apartment 47") == "47"
    assert extract_abode_number("") == ""


def test_loqate_shanklin_empty_abode():
    mapping = map_loqate_address(SHANKLIN, abode_mode="empty")
    report = loqate_report(SHANKLIN, abode_mode="empty")
    current = report["connectCurrent"]
    assert current["subBuilding"] == "Flat 8"
    assert current["abodeNo"] == ""
    assert current["buildingName"] == "Shanklin Towers"
    assert current["buildingNo"] == ""
    assert current["street"] == "Prospect Road"
    assert current["city"] == "Shanklin"
    assert current["subStreet"] == ""
    assert mapping.parseable is True
    assert "loqate_missing_postcode" in mapping.warnings


def test_loqate_abode_modes():
    mirror = loqate_report(SHANKLIN, abode_mode="mirror")["connectCurrent"]
    number = loqate_report(SHANKLIN, abode_mode="number")["connectCurrent"]
    assert mirror["abodeNo"] == "Flat 8"
    assert mirror["subBuilding"] == "Flat 8"
    assert number["abodeNo"] == "8"
    assert number["subBuilding"] == "Flat 8"
