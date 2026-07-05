"""
Resolving a CLI-provided person identifier, and describing the path
between two individuals as a chain of relationships.

Deliberately scoped: this describes the *chain* ("child of ... spouse of
... parent of ...") rather than naming a canonical relationship ("second
cousin once removed"). The latter is a genuinely harder problem with its
own edge cases (half-siblings, step-relations, multiple marriages) --
worth tackling separately once chain-walking is solid.
"""

from __future__ import annotations

import networkx as nx

from gedcomtoolkit.models import FamilyTree, Individual
from gedcomtoolkit.search import find_individuals_by_name


class PersonNotFoundError(Exception):
    """Raised when an identifier matches no individual in the tree."""


class AmbiguousPersonError(Exception):
    """Raised when a name matches more than one individual."""

    def __init__(self, query: str, candidates: list[Individual]):
        self.query = query
        self.candidates = candidates
        super().__init__(query)


def resolve_person(tree: FamilyTree, identifier: str) -> Individual:
    """
    Resolve a CLI-provided identifier to a single Individual.

    Accepts a raw xref_id (e.g. "@I1@") or a name. Raises
    AmbiguousPersonError if a name matches more than one individual,
    PersonNotFoundError if it matches none.
    """
    identifier = identifier.strip()

    if identifier.startswith("@") and identifier.endswith("@"):
        indi = tree.get_individual(identifier)
        if indi is None:
            raise PersonNotFoundError(identifier)
        return indi

    matches = find_individuals_by_name(tree, identifier)
    if not matches:
        raise PersonNotFoundError(identifier)
    if len(matches) > 1:
        raise AmbiguousPersonError(identifier, matches)
    return matches[0]


def describe_relationship_path(
    tree: FamilyTree, g: nx.DiGraph, start_id: str, end_id: str
) -> list[tuple[str, str, str]] | None:
    """
    Return the path from start_id to end_id as a list of
    (from_name, label, to_name) triples, or None if no path exists
    (e.g. the two individuals are in disconnected parts of the tree).
    """
    undirected = nx.Graph()
    undirected.add_nodes_from(g.nodes())
    undirected.add_edges_from(g.edges())

    try:
        path = nx.shortest_path(undirected, start_id, end_id)
    except nx.NetworkXNoPath:
        return None

    steps = []
    for u, v in zip(path[:-1], path[1:]):
        label = _edge_label(g, u, v)
        steps.append((tree.get_individual(u).full_name, label, tree.get_individual(v).full_name))
    return steps


def _edge_label(g: nx.DiGraph, u: str, v: str) -> str:
    """Describe the u -> v step: how is v related to u?"""
    if g.has_edge(u, v):
        relation = g.get_edge_data(u, v)["relation"]
        if relation == "parent":
            return "parent of"
        if relation == "spouse":
            return "spouse of"
    if g.has_edge(v, u):
        relation = g.get_edge_data(v, u)["relation"]
        if relation == "parent":
            return "child of"
    return "related to"
