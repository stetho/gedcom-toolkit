from pathlib import Path

import pytest

from gedcomtoolkit.graph import build_graph
from gedcomtoolkit.parser import parse_gedcom
from gedcomtoolkit.research import find_research_candidates

RESEARCH_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "research.ged"

# research.ged, hand-computed against current_year=2026:
#
# @I1@ Root One:   no birth date (3), no parents linked (5) = 8
#                  descendants: I3, I6, I4, I5 = 4  ->  score = 8 * (1+4) = 40
# @I2@ Root Two:   no death date, b.1920 age 106 (2), no parents linked (5) = 7
#                  descendants: same 4  ->  score = 7 * (1+4) = 35
# @I3@ Child One:  birth+death+parents all present -> no gaps -> excluded
# @I4@ Grandchild One: no birth date (3), parents linked, no descendants
#                  -> score = 3 * (1+0) = 3
# @I5@ Grandchild Two: birth+death+parents all present -> no gaps -> excluded
# @I6@ Child Two:  b.1900, no death date, age 126 (2), parents linked, no descendants
#                  -> score = 2 * (1+0) = 2


@pytest.fixture
def candidates():
    tree = parse_gedcom(RESEARCH_GEDCOM)
    g = build_graph(tree)
    return find_research_candidates(tree, g, current_year=2026)


def test_excludes_individuals_with_no_gaps(candidates):
    ids = {c.individual.xref_id for c in candidates}
    assert "@I3@" not in ids
    assert "@I5@" not in ids


def test_includes_individuals_with_gaps(candidates):
    ids = {c.individual.xref_id for c in candidates}
    assert ids == {"@I1@", "@I2@", "@I4@", "@I6@"}


def test_scores_match_hand_calculation(candidates):
    scores = {c.individual.xref_id: c.score for c in candidates}
    assert scores == {"@I1@": 40, "@I2@": 35, "@I4@": 3, "@I6@": 2}


def test_ranked_highest_score_first(candidates):
    ids_in_order = [c.individual.xref_id for c in candidates]
    assert ids_in_order == ["@I1@", "@I2@", "@I4@", "@I6@"]


def test_descendant_counts(candidates):
    by_id = {c.individual.xref_id: c for c in candidates}
    assert by_id["@I1@"].descendant_count == 4
    assert by_id["@I2@"].descendant_count == 4
    assert by_id["@I4@"].descendant_count == 0
    assert by_id["@I6@"].descendant_count == 0


def test_gap_descriptions(candidates):
    by_id = {c.individual.xref_id: c for c in candidates}
    assert by_id["@I1@"].gaps == ["no birth date", "no parents linked"]
    assert by_id["@I2@"].gaps == ["no death date (likely deceased)", "no parents linked"]
    assert by_id["@I4@"].gaps == ["no birth date"]
    assert by_id["@I6@"].gaps == ["no death date (likely deceased)"]


def test_sample_ged_scores_match_hand_calculation():
    """
    sample.ged, hand-computed against current_year=2026:

    @I1@ John Smith: b.1900,d.1970,no parents linked -> gap: no parents (5)
                      descendants: Alice(@I3@), Carol(@I5@) = 2
                      score = 5 * (1+2) = 15
    @I2@ Mary Jones:  b.1902,no death (age 124, likely deceased, 2),
                      no parents linked (5) = 7
                      descendants: same 2  ->  score = 7 * (1+2) = 21
    @I3@ Alice Smith: b.1925,no death (age 101, likely deceased, 2),
                      parents linked -> gap total 2
                      descendants: Carol(@I5@) = 1  ->  score = 2 * (1+1) = 4
    @I4@ Bob Brown:   b.1922,no death (age 104, likely deceased, 2),
                      no parents linked (5) = 7
                      descendants: Carol(@I5@) = 1  ->  score = 7 * (1+1) = 14
    @I5@ Carol Brown: b.1948, no death but only age 78 (below the 90
                      threshold, not flagged), parents linked -> no gaps,
                      excluded
    """
    sample_ged = Path(__file__).parent.parent / "data" / "sample" / "sample.ged"
    tree = parse_gedcom(sample_ged)
    g = build_graph(tree)
    candidates = find_research_candidates(tree, g, current_year=2026)

    scores = {c.individual.xref_id: c.score for c in candidates}
    assert scores == {"@I1@": 15, "@I2@": 21, "@I3@": 4, "@I4@": 14}
    assert "@I5@" not in scores
