"""
Flagging probable duplicate individuals *within a single file* -- distinct
from `merge`, which will compare two separate files.

A real trap here: matching name + close birth year doesn't necessarily mean
a duplicate record. It was common (especially Victorian-era) for a family
to reuse a name after an earlier child died young -- two genuinely
different people can share both a name and a near-identical birth year.
So rather than asserting "duplicate", each candidate pair is reported with
its underlying signals (birth-year gap, whether they share the same
parents) and a note describing what that pattern usually indicates,
leaving the actual judgement to a human.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from gedcomtoolkit.dates import extract_year
from gedcomtoolkit.models import FamilyTree, Individual

MAX_YEAR_DIFF_TO_CONSIDER = 5


@dataclass
class DuplicateCandidate:
    individual_a: Individual
    individual_b: Individual
    year_diff: int | None
    same_parents: bool
    confidence: float
    note: str


def _confidence_and_note(year_diff: int | None, same_parents: bool) -> tuple[float, str]:
    if year_diff is None:
        return 40.0, "Birth year missing on at least one -- confidence based on name match alone."

    if year_diff == 0:
        if same_parents:
            return (
                70.0,
                "Same parents and same birth year -- could be the same child recorded "
                "twice, or twins who were (unusually) given the same name. Verify.",
            )
        return (
            90.0,
            "Same birth year, no shared family link to compare -- if this is the "
            "same person, their family records may need merging.",
        )

    if year_diff <= 2:
        confidence = 60.0
    else:
        confidence = 30.0

    if same_parents:
        note = (
            "Same parents, different birth years -- likely a namesake (a child "
            "named after an earlier sibling), not a duplicate entry, but worth confirming."
        )
    else:
        note = (
            "Different birth years, no shared family link -- weaker signal; "
            "could be unrelated people who happen to share a name."
        )

    return confidence, note


def find_duplicate_candidates(tree: FamilyTree) -> list[DuplicateCandidate]:
    """
    Group individuals by exact (case-insensitive) full name, and for every
    pair within a group, report the signals -- birth-year gap and whether
    they share the same linked parents -- with a note on how to read that
    pattern. Pairs whose birth years are more than MAX_YEAR_DIFF_TO_CONSIDER
    apart are excluded entirely as too unlikely to be either a duplicate or
    a namesake.
    """
    groups: dict[str, list[Individual]] = {}
    for indi in tree.individuals.values():
        name_key = indi.full_name.strip().lower()
        if name_key == "(unknown)":
            continue
        groups.setdefault(name_key, []).append(indi)

    candidates = []
    for group in groups.values():
        if len(group) < 2:
            continue

        for indi_a, indi_b in combinations(group, 2):
            year_a = extract_year(indi_a.birth_date)
            year_b = extract_year(indi_b.birth_date)

            if year_a is not None and year_b is not None:
                year_diff = abs(year_a - year_b)
                if year_diff > MAX_YEAR_DIFF_TO_CONSIDER:
                    continue
            else:
                year_diff = None

            same_parents = (
                indi_a.family_as_child is not None
                and indi_a.family_as_child == indi_b.family_as_child
            )

            confidence, note = _confidence_and_note(year_diff, same_parents)

            candidates.append(
                DuplicateCandidate(
                    individual_a=indi_a,
                    individual_b=indi_b,
                    year_diff=year_diff,
                    same_parents=same_parents,
                    confidence=confidence,
                    note=note,
                )
            )

    candidates.sort(key=lambda c: -c.confidence)
    return candidates
