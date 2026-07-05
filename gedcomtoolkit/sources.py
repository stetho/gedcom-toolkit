"""
How well-evidenced a tree is, as distinct from how complete it is.

An individual can have every date filled in and still be entirely
unsourced -- that's a hobbyist tree, not a credible one. This module
measures source-citation coverage on the events that actually have dates
recorded (an event with no date can't meaningfully be "unsourced"), and
surfaces the individuals/marriages with the most unsourced facts so
there's somewhere concrete to start.
"""

from __future__ import annotations

from dataclasses import dataclass

from gedcomtoolkit.models import FamilyTree, Individual


@dataclass
class SourceStats:
    total_individuals: int
    total_families: int
    births_recorded: int
    births_sourced: int
    deaths_recorded: int
    deaths_sourced: int
    marriages_recorded: int
    marriages_sourced: int

    @staticmethod
    def _rate(sourced: int, recorded: int) -> float | None:
        """Percentage sourced, or None if the event type has no recorded instances at all."""
        if recorded == 0:
            return None
        return 100 * sourced / recorded

    @property
    def birth_source_rate(self) -> float | None:
        return self._rate(self.births_sourced, self.births_recorded)

    @property
    def death_source_rate(self) -> float | None:
        return self._rate(self.deaths_sourced, self.deaths_recorded)

    @property
    def marriage_source_rate(self) -> float | None:
        return self._rate(self.marriages_sourced, self.marriages_recorded)

    @property
    def overall_source_rate(self) -> float | None:
        total_recorded = self.births_recorded + self.deaths_recorded + self.marriages_recorded
        total_sourced = self.births_sourced + self.deaths_sourced + self.marriages_sourced
        return self._rate(total_sourced, total_recorded)


@dataclass
class UnsourcedIndividual:
    individual: Individual
    unsourced_facts: list[str]


@dataclass
class UnsourcedMarriage:
    xref_id: str
    spouse_names: str
    marriage_date: str


def compute_source_stats(tree: FamilyTree) -> SourceStats:
    births_recorded = births_sourced = 0
    deaths_recorded = deaths_sourced = 0
    marriages_recorded = marriages_sourced = 0

    for indi in tree.individuals.values():
        if indi.birth_date:
            births_recorded += 1
            if indi.birth_sourced:
                births_sourced += 1
        if indi.death_date:
            deaths_recorded += 1
            if indi.death_sourced:
                deaths_sourced += 1

    for fam in tree.families.values():
        if fam.marriage_date:
            marriages_recorded += 1
            if fam.marriage_sourced:
                marriages_sourced += 1

    return SourceStats(
        total_individuals=len(tree.individuals),
        total_families=len(tree.families),
        births_recorded=births_recorded,
        births_sourced=births_sourced,
        deaths_recorded=deaths_recorded,
        deaths_sourced=deaths_sourced,
        marriages_recorded=marriages_recorded,
        marriages_sourced=marriages_sourced,
    )


def find_unsourced_individuals(tree: FamilyTree) -> list[UnsourcedIndividual]:
    """
    Individuals with at least one recorded-but-unsourced fact, ranked by
    how many unsourced facts they have (most first).
    """
    results = []
    for indi in tree.individuals.values():
        gaps = []
        if indi.birth_date and not indi.birth_sourced:
            gaps.append(f"birth ({indi.birth_date})")
        if indi.death_date and not indi.death_sourced:
            gaps.append(f"death ({indi.death_date})")
        if gaps:
            results.append(UnsourcedIndividual(individual=indi, unsourced_facts=gaps))

    results.sort(key=lambda r: len(r.unsourced_facts), reverse=True)
    return results


def find_unsourced_marriages(tree: FamilyTree) -> list[UnsourcedMarriage]:
    """Marriages with a recorded date but no source citation."""
    results = []
    for fam in tree.families.values():
        if fam.marriage_date and not fam.marriage_sourced:
            spouse_names = " & ".join(
                tree.get_individual(pid).full_name
                for pid in (fam.husband_id, fam.wife_id)
                if pid and tree.get_individual(pid)
            )
            results.append(
                UnsourcedMarriage(
                    xref_id=fam.xref_id,
                    spouse_names=spouse_names or "(unknown spouses)",
                    marriage_date=fam.marriage_date,
                )
            )
    return results
