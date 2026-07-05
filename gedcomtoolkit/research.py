"""
Ranking individuals by how valuable they'd be to research next.

The scoring is deliberately simple and interpretable rather than a
black-box model: each individual is checked for a small set of concrete
data gaps, each gap has a fixed weight, and the total is multiplied by
(1 + descendant count). The multiplier is the actual idea behind "research
next": filling in a gap for someone with fifty descendants benefits every
line hanging off them, while the same gap on a childless leaf only ever
helps that one person.

"No death date" is only counted as a gap when the person would clearly be
implausibly old today if still alive -- otherwise a living relative with
no death date would score identically to a brick wall, which isn't useful.
This uses a lower, softer threshold than validate's implausible-age check
(which flags data errors); here it's a heuristic for "a record is probably
just missing", not a claim that the data is wrong.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as _date

import networkx as nx

from gedcomtoolkit.dates import extract_year
from gedcomtoolkit.graph import parent_only_subgraph
from gedcomtoolkit.models import FamilyTree, Individual

PROBABLY_DECEASED_AGE = 90

WEIGHT_NO_BIRTH_DATE = 3
WEIGHT_NO_DEATH_DATE = 2
WEIGHT_NO_PARENTS_LINKED = 5


@dataclass
class ResearchCandidate:
    individual: Individual
    gaps: list[str]
    descendant_count: int
    score: int


def _gaps_for(indi: Individual, current_year: int) -> list[tuple[str, int]]:
    gaps = []

    if not indi.birth_date:
        gaps.append(("no birth date", WEIGHT_NO_BIRTH_DATE))

    if not indi.death_date:
        birth_year = extract_year(indi.birth_date)
        if birth_year is not None and (current_year - birth_year) >= PROBABLY_DECEASED_AGE:
            gaps.append(("no death date (likely deceased)", WEIGHT_NO_DEATH_DATE))

    if not indi.family_as_child:
        gaps.append(("no parents linked", WEIGHT_NO_PARENTS_LINKED))

    return gaps


def find_research_candidates(
    tree: FamilyTree, g: nx.DiGraph, current_year: int | None = None
) -> list[ResearchCandidate]:
    """
    Return individuals with at least one data gap, ranked highest-priority
    first. Individuals with no detected gaps are excluded entirely.
    """
    current_year = current_year or _date.today().year
    parent_graph = parent_only_subgraph(g)

    candidates = []
    for indi in tree.individuals.values():
        gap_pairs = _gaps_for(indi, current_year)
        if not gap_pairs:
            continue

        descendant_count = len(nx.descendants(parent_graph, indi.xref_id))
        gap_weight_total = sum(weight for _desc, weight in gap_pairs)
        score = gap_weight_total * (1 + descendant_count)

        candidates.append(
            ResearchCandidate(
                individual=indi,
                gaps=[desc for desc, _weight in gap_pairs],
                descendant_count=descendant_count,
                score=score,
            )
        )

    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates
