"""Unit tests for UK address normalization (PAL concat-in-street → bureau fields)."""

import pytest

from pp_poc.uk_address_normalization import (
    NormalizedAddress,
    needs_normalization,
    normalize_uk_address_for_bureau,
)


class TestNeedsNormalization:
    def test_empty_street_false(self):
        assert needs_normalization("", "", "", "") is False
        assert needs_normalization("   ", "", "", "") is False

    def test_structured_fields_skip(self):
        assert needs_normalization("Norlington Road", "First Floor Flat 2", "", "") is False
        assert needs_normalization("High Street", "", "", "105") is False
        assert needs_normalization("High Street", "", "Oak House", "") is False

    def test_concat_street_true(self):
        assert needs_normalization("63 Tarvin Road", "", "", "") is True


class TestNormalizeUkAddressForBureau:
    @pytest.mark.parametrize(
        "street,expected",
        [
            (
                "63 Tarvin Road",
                NormalizedAddress(
                    sub_building="",
                    building_name="",
                    building_number="63",
                    street="Tarvin Road",
                ),
            ),
            (
                "13 Witham Gardens",
                NormalizedAddress(
                    sub_building="",
                    building_name="",
                    building_number="13",
                    street="Witham Gardens",
                ),
            ),
            (
                "286 Oundle Road",
                NormalizedAddress(
                    sub_building="",
                    building_name="",
                    building_number="286",
                    street="Oundle Road",
                ),
            ),
            (
                "Flat 2 The Old Bakery 11 Dollar Street",
                NormalizedAddress(
                    sub_building="Flat 2",
                    building_name="The Old Bakery",
                    building_number="11",
                    street="Dollar Street",
                ),
            ),
            (
                "Branton House 3 200 Becontree Avenue",
                NormalizedAddress(
                    sub_building="3",
                    building_name="Branton House",
                    building_number="200",
                    street="Becontree Avenue",
                ),
            ),
            (
                "Flat 6",
                NormalizedAddress(
                    sub_building="Flat 6",
                    building_name="",
                    building_number="",
                    street="",
                ),
            ),
            (
                "4 Flat",
                NormalizedAddress(
                    sub_building="4 Flat",
                    building_name="",
                    building_number="",
                    street="",
                ),
            ),
        ],
    )
    def test_concat_street_cases(self, street, expected):
        """PAL concat-in-street blobs normalize into semantic bureau fields."""
        result = normalize_uk_address_for_bureau(street=street)
        assert result == expected

    def test_structured_flat_passthrough(self):
        result = normalize_uk_address_for_bureau(
            street="Norlington Road",
            flat="First Floor Flat 2",
        )
        assert result == NormalizedAddress(
            sub_building="First Floor Flat 2",
            building_name="",
            building_number="",
            street="Norlington Road",
        )

    def test_structured_house_number_passthrough(self):
        result = normalize_uk_address_for_bureau(
            street="High Street",
            house_number=105,
        )
        assert result == NormalizedAddress(
            sub_building="",
            building_name="",
            building_number="105",
            street="High Street",
        )

    def test_collapses_whitespace(self):
        result = normalize_uk_address_for_bureau(street="  63   Tarvin   Road  ")
        assert result.building_number == "63"
        assert result.street == "Tarvin Road"
