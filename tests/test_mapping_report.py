"""JSON mapping report used by the terminal demo command."""

import json
from pathlib import Path

from pp_poc.mapping_report import mapping_report, mapping_report_batch

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_single_matt_example_json_shape():
    report = mapping_report(
        address1="138 Belsize Road, flat 2",
        town="LONDON",
        postcode="NW3 4BA",
    )
    assert report["confidence"] in ("high", "medium", "low")
    assert "connectCurrent" not in report
    assert report["verifyCurrent"]["buildingNo"] == "138"
    assert report["verifyCurrent"]["street"] == "Belsize Road"
    assert report["verifyCurrent"]["subBuilding"] == "flat 2"
    assert report["verifyCurrent"]["town"] == "LONDON"
    assert report["verifyCurrent"]["addressLine"] == ""
    assert report["verifyCurrent"]["buildingName"] == ""
    assert "request" not in report
    json.dumps(report)


def test_full_request_included_when_asked():
    report = mapping_report(
        address1="56, Westcroft Close",
        town="LONDON",
        postcode="SW1A 1AA",
        full_request=True,
        target="identitysearch",
    )
    assert report["request"]["products"] == ["AML"]
    assert report["request"]["common"]["person"]["addresses"]["current"]["buildingNo"] == "56"
    assert report["connectCurrent"]["subStreet"] == ""
    assert "_mappingMeta" not in report["request"]


def test_matt_examples_fixture_batch():
    cases = json.loads((FIXTURES / "matt_examples.json").read_text(encoding="utf-8"))
    batch = mapping_report_batch(cases, full_request=True, target="verify")
    assert batch["summary"]["total"] == 2
    assert batch["summary"]["high_medium_pct"] == 100.0
    by_id = {row["id"]: row for row in batch["results"]}
    belsize = by_id["matt_belsize_flat_after_road"]
    westcroft = by_id["matt_westcroft_stray_comma"]
    assert belsize["verifyCurrent"]["subBuilding"] == "flat 2"
    assert belsize["verifyCurrent"]["addressLine"] == ""
    assert westcroft["verifyCurrent"]["buildingNo"] == "56"
    req = belsize["request"]
    assert req["firstName"] == ""
    assert req["lastName"] == ""
    assert req["dateOfBirth"] == ""
    assert req["reasonForSearch"] == ""
    assert req["middleName"] == ""
    assert req["title"] == ""
    assert req["addresses"]["previousAddresses"] == []
    assert "connectCurrent" not in belsize
