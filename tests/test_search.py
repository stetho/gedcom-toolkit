from pathlib import Path

import pytest

from gedcomtoolkit.parser import parse_gedcom
from gedcomtoolkit.search import find_individuals_by_name

AMBIGUOUS_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "ambiguous.ged"


@pytest.fixture
def ambiguous_tree():
    return parse_gedcom(AMBIGUOUS_GEDCOM)


def test_returns_all_matches_for_ambiguous_name(ambiguous_tree):
    matches = find_individuals_by_name(ambiguous_tree, "Bob Smith")
    assert len(matches) == 3
    assert {m.xref_id for m in matches} == {"@I1@", "@I2@", "@I3@"}


def test_matches_are_sorted_by_birth_year(ambiguous_tree):
    matches = find_individuals_by_name(ambiguous_tree, "Bob Smith")
    years = [m.birth_date for m in matches]
    assert years == ["28 AUG 1908", "1935", "30 JUN 1957"]


def test_case_insensitive(ambiguous_tree):
    matches = find_individuals_by_name(ambiguous_tree, "bob smith")
    assert len(matches) == 3


def test_partial_name_match(ambiguous_tree):
    matches = find_individuals_by_name(ambiguous_tree, "Alice")
    assert len(matches) == 1
    assert matches[0].xref_id == "@I4@"


def test_no_match_returns_empty_list(ambiguous_tree):
    assert find_individuals_by_name(ambiguous_tree, "Nobody Here") == []


def test_empty_query_returns_empty_list(ambiguous_tree):
    assert find_individuals_by_name(ambiguous_tree, "") == []
    assert find_individuals_by_name(ambiguous_tree, "   ") == []


def test_sample_tree_unambiguous_lookup(sample_tree):
    """Using the existing sample.ged fixture too, since it has no
    duplicate names -- a useful contrast to the ambiguous fixture."""
    matches = find_individuals_by_name(sample_tree, "Smith")
    assert len(matches) == 2  # John Smith and Alice Smith
