from pathlib import Path

import pytest

from gedcomtoolkit.duplicates import find_duplicate_candidates
from gedcomtoolkit.parser import parse_gedcom

DUPLICATES_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "duplicates.ged"

# duplicates.ged cases:
#
# @I1@/@I2@ "Someone Duplicate": both b.1900, no parents linked
#   -> year_diff=0, same_parents=False -> confidence 90
# @I3@/@I4@ "Namesake Child": b.1920/b.1923 (gap 3), same parents (@F1@)
#   -> year_diff=3, same_parents=True -> confidence 30 (gap > 2)
# @I5@/@I6@ "Missingdata Twin": one has no birth date, same parents (@F2@)
#   -> year_diff=None -> confidence 40
# @I7@/@I8@ "Far Apart": b.1800/b.1950 (gap 150) -> excluded entirely
# @I9@ "Solo Person": unique name -> no pair, not in results
# @I10@/@I11@ "Case Test"/"CASE TEST": b.1980/b.1980, no parents linked
#   -> case-insensitive name match -> year_diff=0, same_parents=False -> confidence 90


@pytest.fixture
def candidates():
    tree = parse_gedcom(DUPLICATES_GEDCOM)
    return find_duplicate_candidates(tree)


def test_far_apart_pair_excluded(candidates):
    names = {c.individual_a.full_name for c in candidates} | {
        c.individual_b.full_name for c in candidates
    }
    assert "Far Apart" not in names


def test_solo_person_not_included(candidates):
    names = {c.individual_a.full_name for c in candidates} | {
        c.individual_b.full_name for c in candidates
    }
    assert "Solo Person" not in names


def test_same_year_no_parents_confidence(candidates):
    match = next(c for c in candidates if c.individual_a.full_name == "Someone Duplicate")
    assert match.year_diff == 0
    assert match.same_parents is False
    assert match.confidence == 90.0


def test_namesake_pattern_confidence(candidates):
    match = next(c for c in candidates if c.individual_a.full_name == "Namesake Child")
    assert match.year_diff == 3
    assert match.same_parents is True
    assert match.confidence == 30.0
    assert "namesake" in match.note.lower()


def test_missing_birth_year_confidence(candidates):
    match = next(c for c in candidates if c.individual_a.full_name == "Missingdata Twin")
    assert match.year_diff is None
    assert match.same_parents is True
    assert match.confidence == 40.0


def test_case_insensitive_name_grouping(candidates):
    # "Case Test" and "CASE TEST" should be grouped as the same name
    matches = [c for c in candidates if c.individual_a.xref_id in ("@I10@", "@I11@")]
    assert len(matches) == 1
    assert matches[0].year_diff == 0
    assert matches[0].confidence == 90.0


def test_sorted_highest_confidence_first(candidates):
    confidences = [c.confidence for c in candidates]
    assert confidences == sorted(confidences, reverse=True)


def test_total_candidate_count(candidates):
    # 4 pairs total: Someone Duplicate, Namesake Child, Missingdata Twin, Case Test
    assert len(candidates) == 4
