"""Tests for legacy address mapping (Matt examples + comma edge cases)."""

from pp_poc.legacy_mapper import map_legacy_address
from pp_poc.legacy_preprocess import preprocess_legacy_line


class TestPreprocessLegacyLine:
    def test_trailing_flat_after_street(self):
        blob, flat, warnings = preprocess_legacy_line("138 Belsize Road, flat 2")
        assert blob == "138 Belsize Road"
        assert flat.lower() == "flat 2"
        assert "trailing_flat_extracted" in warnings

    def test_number_comma_street(self):
        blob, flat, warnings = preprocess_legacy_line("56, Westcroft Close")
        assert blob == "56 Westcroft Close"
        assert flat == ""
        assert "comma_normalised" in warnings


class TestMapLegacyAddressMattExamples:
    def test_belsize_road_flat_2(self):
        result = map_legacy_address(
            address1="138 Belsize Road, flat 2",
            town="LONDON",
            county="United Kingdom",
            postcode="NW3 4BA",
        )
        current = result.mapped.to_connect_dict()
        assert current["buildingNo"] == "138"
        assert current["street"] == "Belsize Road"
        assert current["abodeNo"] == "flat 2"
        assert current["city"] == "LONDON"
        assert current["postCode"] == "NW3 4BA"
        assert result.parseable is True

    def test_westcroft_close_stray_comma(self):
        result = map_legacy_address(
            address1="56, Westcroft Close",
            town="LONDON",
            county="UK",
            postcode="SW1A 1AA",
        )
        current = result.mapped.to_connect_dict()
        assert current["buildingNo"] == "56"
        assert current["street"] == "Westcroft Close"
        assert result.parseable is True
        assert "comma_normalised" in result.warnings

    def test_address2_merged(self):
        result = map_legacy_address(
            address1="10 High Street",
            address2="Flat 3",
            town="Cardiff",
            postcode="CF10 1AA",
        )
        current = result.mapped.to_connect_dict()
        assert current["buildingNo"] == "10"
        assert current["street"] == "High Street"

    def test_empty_address_not_parseable(self):
        result = map_legacy_address(address1="", town="London")
        assert result.parseable is False
        assert "empty_address_lines" in result.warnings
