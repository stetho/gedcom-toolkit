"""
Name-based lookup across a FamilyTree.

Deliberately separate from any one command: findid uses this directly, and
findrelationship (roadmap) will fall back to it when given a name instead of
an xref_id, so the disambiguation behaviour only needs to exist in one place.
"""

from __future__ import annotations

from gedcomtoolkit.dates import extract_year
from gedcomtoolkit.models import FamilyTree, Individual


def find_individuals_by_name(tree: FamilyTree, query: str) -> list[Individual]:
    """
    Case-insensitive substring match against each individual's full name.

    GEDCOM names aren't unique -- this deliberately returns every match
    rather than guessing, so the caller (a CLI command, or another command
    disambiguating a name) can show all candidates and let a human pick.

    Results are sorted by birth year (unknown birth years last) so that,
    e.g., a great-grandfather and his father come back in a sensible order
    rather than dict/insertion order.
    """
    query_lower = query.strip().lower()
    if not query_lower:
        return []

    matches = [
        indi for indi in tree.individuals.values() if query_lower in indi.full_name.lower()
    ]

    def sort_key(indi: Individual) -> tuple[bool, int]:
        year = extract_year(indi.birth_date)
        return (year is None, year or 0)

    return sorted(matches, key=sort_key)
