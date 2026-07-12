"""
Plain dataclasses for the domain model.

Deliberately decoupled from ged4py's own record objects: everything downstream
(graph building, commands, tests) works against these simple types instead of
reaching back into the parsing library. If the parser is ever swapped out,
only parser.py needs to change.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Individual:
    xref_id: str
    given: str | None = None
    surname: str | None = None
    sex: str | None = None  # "M", "F", or None
    birth_date: str | None = None  # kept as raw GEDCOM date string for now
    death_date: str | None = None
    birth_sourced: bool = False
    death_sourced: bool = False
    birth_place: str | None = None
    death_place: str | None = None
    family_as_child: str | None = None  # xref_id of FAM they're a child in
    families_as_spouse: list[str] = field(default_factory=list)  # xref_ids of FAM

    @property
    def full_name(self) -> str:
        parts = [p for p in (self.given, self.surname) if p]
        return " ".join(parts) if parts else "(unknown)"

    @property
    def is_living(self) -> bool:
        """Best-effort guess: no recorded death and no death date."""
        return self.death_date is None


@dataclass
class Family:
    xref_id: str
    husband_id: str | None = None
    wife_id: str | None = None
    marriage_date: str | None = None
    marriage_sourced: bool = False
    marriage_place: str | None = None
    child_ids: list[str] = field(default_factory=list)


@dataclass
class FamilyTree:
    """Container for a fully-parsed GEDCOM file."""

    individuals: dict[str, Individual] = field(default_factory=dict)
    families: dict[str, Family] = field(default_factory=dict)

    def get_individual(self, xref_id: str) -> Individual | None:
        return self.individuals.get(xref_id)

    def get_family(self, xref_id: str) -> Family | None:
        return self.families.get(xref_id)
