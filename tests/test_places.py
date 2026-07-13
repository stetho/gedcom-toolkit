from pathlib import Path

import pytest

from gedcomtoolkit.parser import parse_gedcom
from gedcomtoolkit.places import (
    clean_segments,
    find_place_suggestions,
    is_subsequence,
)

PLACES_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "places.ged"

# places.ged usage counts:
#   Croydon                     2
#   Croydon, Surrey             3
#   Croydon, England            2
#   Croydon,, England           1   (cleans to same segments as "Croydon, England" -> merged, total 3)
#   Croydon, Greater London     4
#   Croydon, Surrey, England    1
#   London                      1
#   London, England             2
#   Brighton, Sussex, England   3   (only one distinct variant -- excluded entirely)
#
# For candidate "Croydon, Surrey, England" (weight from compatible variants):
#   "Croydon" (2) is a subsequence -> +2
#   "Croydon, Surrey" (3) is a subsequence -> +3
#   "Croydon, England" (3, merged) is a subsequence (Croydon..England, skipping Surrey) -> +3
#   "Croydon, Greater London" (4) is NOT a subsequence (Greater London matches nothing) -> conflict
#   compatible weight = 8, total_other = 8 + 4 = 12, confidence = 100 * 8/12 = 66.67%
#
# For "London, England": "London" (1) is a subsequence -> compatible weight 1,
#   total_other = 1, confidence = 100%.


# --- unit tests for the building blocks -------------------------------------


def test_clean_segments_strips_and_drops_empty():
    assert clean_segments("Croydon, Surrey, England") == ("Croydon", "Surrey", "England")
    assert clean_segments("Croydon,, England") == ("Croydon", "England")
    assert clean_segments("  Croydon  ") == ("Croydon",)
    assert clean_segments("") == ()


def test_is_subsequence_basic():
    assert is_subsequence(("Croydon",), ("Croydon", "Surrey", "England")) is True
    assert is_subsequence(("Croydon", "England"), ("Croydon", "Surrey", "England")) is True
    assert is_subsequence(("Croydon", "Greater London"), ("Croydon", "Surrey", "England")) is False


def test_is_subsequence_case_insensitive():
    assert is_subsequence(("CROYDON",), ("Croydon", "Surrey")) is True


def test_is_subsequence_longer_than_target_is_false():
    assert is_subsequence(("Croydon", "Surrey", "England"), ("Croydon", "Surrey")) is False


def test_is_subsequence_empty_is_trivially_true():
    assert is_subsequence((), ("Croydon", "Surrey")) is True


# --- integration tests against places.ged -----------------------------------


@pytest.fixture
def suggestions():
    tree = parse_gedcom(PLACES_GEDCOM)
    return find_place_suggestions(tree)


def test_finds_croydon_and_london_clusters_only(suggestions):
    keys = {s.primary_key for s in suggestions}
    assert keys == {"croydon", "london"}  # brighton excluded: only one distinct variant


def test_croydon_suggested_canonical(suggestions):
    croydon = next(s for s in suggestions if s.primary_key == "croydon")
    assert croydon.suggested_canonical == "Croydon, Surrey, England"
    assert croydon.canonical_count == 1  # rare form -- worth surfacing, not hiding


def test_croydon_confidence(suggestions):
    croydon = next(s for s in suggestions if s.primary_key == "croydon")
    assert croydon.confidence == pytest.approx(66.666, abs=0.01)


def test_croydon_compatible_variants(suggestions):
    croydon = next(s for s in suggestions if s.primary_key == "croydon")
    compatible = dict(croydon.compatible_variants)
    assert compatible == {
        "Croydon, Surrey": 3,
        "Croydon, England": 3,  # merged: 2 + the doubled-comma variant's 1
        "Croydon": 2,
    }


def test_croydon_conflicting_variant_is_greater_london(suggestions):
    croydon = next(s for s in suggestions if s.primary_key == "croydon")
    assert croydon.conflicting_variants == [("Croydon, Greater London", 4)]


def test_london_cluster(suggestions):
    london = next(s for s in suggestions if s.primary_key == "london")
    assert london.suggested_canonical == "London, England"
    assert london.canonical_count == 2
    assert london.confidence == 100.0
    assert london.compatible_variants == [("London", 1)]
    assert london.conflicting_variants == []
