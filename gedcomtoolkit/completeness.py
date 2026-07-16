"""
Per-generation completeness of parent linkage.

"Generation" here means depth from the nearest known root in an
individual's own ancestor line, not absolute chronological era: someone
with zero known parents is always generation 0 for this report, even if
they're a 20th-century person whose parents just haven't been researched
yet, rather than a genuine centuries-old founding ancestor. Different
disconnected lines in the same file can therefore have very different real
eras both labelled "generation 0". This mirrors how genealogy software
generally numbers generations (depth from the nearest known ancestor gap)
and is called out here so the report isn't misread as an absolute
timeline.

A direct consequence: generation 0 will always show 100% "no parents
linked" -- that's structurally guaranteed (anyone with a known parent
can't be generation 0), not a finding.

Requires the parent-only graph to be acyclic. If validate hasn't been run
recently, run it first -- this mirrors validate being first on the
project roadmap for the same reason `rn` depends on it.
"""

from __future__ import annotations

from dataclasses import dataclass

import networkx as nx

from gedcomtoolkit.graph import parent_only_subgraph
from gedcomtoolkit.models import FamilyTree, Individual


class CyclicTreeError(Exception):
    """Raised when the parent graph contains a cycle -- generations can't be computed."""


def compute_generations(g: nx.DiGraph) -> dict[str, int]:
    """
    Generation number for every individual: 0 for anyone with no known
    parent, otherwise 1 + the deepest of their parents' generations (using
    the deepest rather than any single parent so that lines of unequal
    length converging through marriage are handled sensibly).
    """
    parent_graph = parent_only_subgraph(g)

    try:
        order = list(nx.topological_sort(parent_graph))
    except nx.NetworkXUnfeasible as exc:
        raise CyclicTreeError(
            "The parent graph contains a cycle -- run `gedcom validate` first."
        ) from exc

    generations: dict[str, int] = {}
    for node in order:
        parents = list(parent_graph.predecessors(node))
        generations[node] = 0 if not parents else 1 + max(generations[p] for p in parents)

    return generations


def _parent_count(tree: FamilyTree, indi: Individual) -> int:
    if indi.family_as_child is None:
        return 0
    fam = tree.get_family(indi.family_as_child)
    if fam is None:
        return 0
    return sum(1 for pid in (fam.husband_id, fam.wife_id) if pid)


@dataclass
class GenerationCompleteness:
    generation: int
    total: int
    both_parents: int
    one_parent: int
    no_parents: int

    @property
    def both_pct(self) -> float:
        return 100 * self.both_parents / self.total if self.total else 0.0

    @property
    def one_pct(self) -> float:
        return 100 * self.one_parent / self.total if self.total else 0.0

    @property
    def none_pct(self) -> float:
        return 100 * self.no_parents / self.total if self.total else 0.0


def compute_completeness(tree: FamilyTree, g: nx.DiGraph) -> list[GenerationCompleteness]:
    generations = compute_generations(g)

    buckets: dict[int, dict[str, int]] = {}
    for xref_id, indi in tree.individuals.items():
        gen = generations.get(xref_id, 0)
        bucket = buckets.setdefault(gen, {"total": 0, "both": 0, "one": 0, "none": 0})
        bucket["total"] += 1

        count = _parent_count(tree, indi)
        if count == 2:
            bucket["both"] += 1
        elif count == 1:
            bucket["one"] += 1
        else:
            bucket["none"] += 1

    return [
        GenerationCompleteness(
            generation=gen,
            total=b["total"],
            both_parents=b["both"],
            one_parent=b["one"],
            no_parents=b["none"],
        )
        for gen, b in sorted(buckets.items())
    ]
