"""
Data-quality checks for a parsed GEDCOM file.

Structured as a small rule engine (same pattern as ha-blind-spots): each
rule is a function of (tree, graph) -> list[ValidationIssue], and RULES is
just the list of them. Adding a new check later means writing one function
and adding it to RULES -- nothing else changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as _date

import networkx as nx

from gedcomtoolkit.dates import extract_year
from gedcomtoolkit.models import FamilyTree

MAX_PLAUSIBLE_AGE = 110
MIN_PARENT_CHILD_GAP_YEARS = 10
MAX_POSTHUMOUS_BIRTH_YEARS = 1  # allows a child born shortly after a parent's death

CATEGORIES = [
    "cycle",
    "death_before_birth",
    "implausible_age",
    "parent_child_timing",
]


@dataclass
class ValidationIssue:
    severity: str  # "error" or "warning"
    category: str
    message: str


def _cycle_check(tree: FamilyTree, g: nx.DiGraph) -> list[ValidationIssue]:
    parent_edges = [(u, v) for u, v, d in g.edges(data=True) if d["relation"] == "parent"]
    parent_graph = nx.DiGraph(parent_edges)
    parent_graph.add_nodes_from(g.nodes())

    if nx.is_directed_acyclic_graph(parent_graph):
        return []

    cycle = nx.find_cycle(parent_graph)
    names = [tree.get_individual(u).full_name for u, _v in cycle]
    chain = " -> ".join(names + [names[0]])
    return [
        ValidationIssue(
            severity="error",
            category="cycle",
            message=f"Cycle in ancestry (someone is recorded as their own ancestor): {chain}",
        )
    ]


def _death_before_birth(tree: FamilyTree, g: nx.DiGraph) -> list[ValidationIssue]:
    issues = []
    for indi in tree.individuals.values():
        birth_year = extract_year(indi.birth_date)
        death_year = extract_year(indi.death_date)
        if birth_year is not None and death_year is not None and death_year < birth_year:
            issues.append(
                ValidationIssue(
                    severity="error",
                    category="death_before_birth",
                    message=(
                        f"{indi.full_name} ({indi.xref_id}): "
                        f"death year {death_year} is before birth year {birth_year}"
                    ),
                )
            )
    return issues


def _implausible_age(
    tree: FamilyTree, g: nx.DiGraph, current_year: int | None = None
) -> list[ValidationIssue]:
    current_year = current_year or _date.today().year
    issues = []
    for indi in tree.individuals.values():
        birth_year = extract_year(indi.birth_date)
        if birth_year is None:
            continue

        death_year = extract_year(indi.death_date)
        if death_year is not None:
            age_at_death = death_year - birth_year
            if age_at_death > MAX_PLAUSIBLE_AGE:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        category="implausible_age",
                        message=(
                            f"{indi.full_name} ({indi.xref_id}): "
                            f"recorded age at death is {age_at_death} years"
                        ),
                    )
                )
        else:
            age_if_alive = current_year - birth_year
            if age_if_alive > MAX_PLAUSIBLE_AGE:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        category="implausible_age",
                        message=(
                            f"{indi.full_name} ({indi.xref_id}): no death recorded, "
                            f"would be {age_if_alive} years old today "
                            "-- check for a missing death record"
                        ),
                    )
                )
    return issues


def _parent_child_timing(tree: FamilyTree, g: nx.DiGraph) -> list[ValidationIssue]:
    issues = []
    for fam in tree.families.values():
        for parent_id in (fam.husband_id, fam.wife_id):
            parent = tree.get_individual(parent_id) if parent_id else None
            if parent is None:
                continue

            parent_birth = extract_year(parent.birth_date)
            parent_death = extract_year(parent.death_date)

            for child_id in fam.child_ids:
                child = tree.get_individual(child_id)
                if child is None:
                    continue

                child_birth = extract_year(child.birth_date)
                if child_birth is None:
                    continue

                if (
                    parent_birth is not None
                    and child_birth - parent_birth < MIN_PARENT_CHILD_GAP_YEARS
                ):
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            category="parent_child_timing",
                            message=(
                                f"{parent.full_name} ({parent.xref_id}) would have been "
                                f"{child_birth - parent_birth} years old when "
                                f"{child.full_name} ({child.xref_id}) was born"
                            ),
                        )
                    )

                if (
                    parent_death is not None
                    and child_birth - parent_death > MAX_POSTHUMOUS_BIRTH_YEARS
                ):
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            category="parent_child_timing",
                            message=(
                                f"{child.full_name} ({child.xref_id}) born "
                                f"{child_birth - parent_death} years after "
                                f"{parent.full_name} ({parent.xref_id}) died"
                            ),
                        )
                    )
    return issues


RULES = [
    _cycle_check,
    _death_before_birth,
    _implausible_age,
    _parent_child_timing,
]


def run_validation(tree: FamilyTree, g: nx.DiGraph) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for rule in RULES:
        issues.extend(rule(tree, g))
    return issues
