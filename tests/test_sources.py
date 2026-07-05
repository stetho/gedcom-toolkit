from pathlib import Path

import pytest

from gedcomtoolkit.parser import parse_gedcom
from gedcomtoolkit.sources import (
    compute_source_stats,
    find_unsourced_individuals,
    find_unsourced_marriages,
)

SOURCES_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "sources.ged"

# sources.ged, hand-computed:
#
# @I1@ Test One:   birth 1900 (sourced), death 1970 (sourced)      -> fully sourced
# @I2@ Test Two:   birth 1905 (sourced), death 1975 (unsourced)
# @I3@ Test Three: birth 1930 (unsourced), death 2000 (sourced)
# @I4@ Test Four:  birth 1932 (unsourced), no death recorded
# @I5@ Test Five:  no birth recorded, death 1990 (unsourced)
# @I6@ Test Six:   no birth, no death -- excluded from every count
#
# Births recorded: I1,I2,I3,I4 = 4; sourced: I1,I2 = 2  -> 50%
# Deaths recorded: I1,I2,I3,I5 = 4; sourced: I1,I3 = 2  -> 50%
# Marriages recorded: F1 (sourced), F2 (unsourced) = 2; sourced = 1 -> 50%
# Overall: 10 recorded, 5 sourced -> 50%


@pytest.fixture
def tree():
    return parse_gedcom(SOURCES_GEDCOM)


def test_births_stats(tree):
    stats = compute_source_stats(tree)
    assert stats.births_recorded == 4
    assert stats.births_sourced == 2
    assert stats.birth_source_rate == 50.0


def test_deaths_stats(tree):
    stats = compute_source_stats(tree)
    assert stats.deaths_recorded == 4
    assert stats.deaths_sourced == 2
    assert stats.death_source_rate == 50.0


def test_marriage_stats(tree):
    stats = compute_source_stats(tree)
    assert stats.marriages_recorded == 2
    assert stats.marriages_sourced == 1
    assert stats.marriage_source_rate == 50.0


def test_overall_rate(tree):
    stats = compute_source_stats(tree)
    assert stats.overall_source_rate == 50.0


def test_rate_is_none_when_nothing_recorded():
    # An event type with zero recorded instances shouldn't claim a 0% rate
    # (which would look like "totally unsourced" rather than "not applicable").
    from gedcomtoolkit.sources import SourceStats

    stats = SourceStats(
        total_individuals=1,
        total_families=0,
        births_recorded=0,
        births_sourced=0,
        deaths_recorded=0,
        deaths_sourced=0,
        marriages_recorded=0,
        marriages_sourced=0,
    )
    assert stats.birth_source_rate is None
    assert stats.overall_source_rate is None


def test_unsourced_individuals(tree):
    results = find_unsourced_individuals(tree)
    by_id = {r.individual.xref_id: r for r in results}

    assert "@I1@" not in by_id  # fully sourced
    assert "@I6@" not in by_id  # no facts at all

    assert by_id["@I2@"].unsourced_facts == ["death (1975)"]
    assert by_id["@I3@"].unsourced_facts == ["birth (1930)"]
    assert by_id["@I4@"].unsourced_facts == ["birth (1932)"]
    assert by_id["@I5@"].unsourced_facts == ["death (1990)"]


def test_unsourced_marriages(tree):
    results = find_unsourced_marriages(tree)
    assert len(results) == 1
    assert results[0].xref_id == "@F2@"
    assert results[0].marriage_date == "1955"
    assert "Test Three" in results[0].spouse_names
    assert "Test Four" in results[0].spouse_names
