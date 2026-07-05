"""
Naming the relationship between two individuals, rather than just
describing the chain between them (see relationship.py).

Approach: find the closest common ancestor of the two people, then use
"how many generations up is each person from that ancestor" to derive the
term (siblings, cousins-N-times-removed, aunts/uncles, great-*, etc.) --
this is the standard genealogical algorithm and handles the full range of
blood relationships correctly, including arbitrary numbers of "greats".

In-law terms are only attempted for the small set that's genuinely
unambiguous in English: a spouse's sibling or parent, and the reverse (a
sibling's or child's spouse). Anything beyond that (e.g. a spouse's
cousin, or a chain with more than one marriage in it) returns None --
callers should fall back to describing the raw chain instead of guessing
at a term that doesn't have solid common usage.

One acknowledged simplification: English kinship terms for collateral
relatives beyond aunt/uncle and niece/nephew aren't fully standardised
("grand-niece" vs "great-niece" are both common). This module always uses
the "great-" prefix, mirroring the lineal great-grandparent/great-grandchild
pattern, for internal consistency.
"""

from __future__ import annotations

import networkx as nx

from gedcomtoolkit.models import FamilyTree

_ORDINALS = {
    1: "first",
    2: "second",
    3: "third",
    4: "fourth",
    5: "fifth",
    6: "sixth",
    7: "seventh",
    8: "eighth",
    9: "ninth",
    10: "tenth",
}


def _ordinal(n: int) -> str:
    return _ORDINALS.get(n, f"{n}th")


def _removed_phrase(n: int) -> str:
    if n == 0:
        return ""
    if n == 1:
        return ", once removed"
    if n == 2:
        return ", twice removed"
    return f", {n} times removed"


def _gendered(sex: str | None, male_word: str, female_word: str, neutral_word: str) -> str:
    if sex == "M":
        return male_word
    if sex == "F":
        return female_word
    return neutral_word


def _ancestor_term(up: int, sex: str | None) -> str:
    if up == 1:
        return _gendered(sex, "father", "mother", "parent")
    base = _gendered(sex, "grandfather", "grandmother", "grandparent")
    greats = up - 2
    return "-".join(["great"] * greats + [base]) if greats > 0 else base


def _descendant_term(down: int, sex: str | None) -> str:
    if down == 1:
        return _gendered(sex, "son", "daughter", "child")
    base = _gendered(sex, "grandson", "granddaughter", "grandchild")
    greats = down - 2
    return "-".join(["great"] * greats + [base]) if greats > 0 else base


def _aunt_uncle_term(up: int, sex: str | None) -> str:
    base = _gendered(sex, "uncle", "aunt", "aunt/uncle")
    greats = up - 2
    return "-".join(["great"] * greats + [base]) if greats > 0 else base


def _niece_nephew_term(up: int, sex: str | None) -> str:
    base = _gendered(sex, "nephew", "niece", "niece/nephew")
    greats = up - 2
    return "-".join(["great"] * greats + [base]) if greats > 0 else base


def _ancestor_distances(g: nx.DiGraph, start: str) -> dict[str, int]:
    """Distance in generations from `start` up to every ancestor (0 = self)."""
    reversed_parent_graph = nx.DiGraph()
    reversed_parent_graph.add_nodes_from(g.nodes())
    for u, v, d in g.edges(data=True):
        if d["relation"] == "parent":
            reversed_parent_graph.add_edge(v, u)  # child -> parent
    return nx.single_source_shortest_path_length(reversed_parent_graph, start)


def _spouses(g: nx.DiGraph, person_id: str) -> list[str]:
    return [v for _u, v, d in g.out_edges(person_id, data=True) if d["relation"] == "spouse"]


def _blood_relationship(tree: FamilyTree, g: nx.DiGraph, id1: str, id2: str) -> str | None:
    """How id2 relates to id1 by blood, or None if they share no ancestor."""
    ancestors_1 = _ancestor_distances(g, id1)
    ancestors_2 = _ancestor_distances(g, id2)
    common = set(ancestors_1) & set(ancestors_2)
    if not common:
        return None

    closest = min(common, key=lambda a: ancestors_1[a] + ancestors_2[a])
    up1, up2 = ancestors_1[closest], ancestors_2[closest]
    sex2 = tree.get_individual(id2).sex

    if up1 == 0 and up2 == 0:
        return None  # same person
    if up1 == 0:
        return _descendant_term(up2, sex2)
    if up2 == 0:
        return _ancestor_term(up1, sex2)
    if up1 == 1 and up2 == 1:
        return _gendered(sex2, "brother", "sister", "sibling")
    if up1 == 1:
        return _niece_nephew_term(up2, sex2)
    if up2 == 1:
        return _aunt_uncle_term(up1, sex2)

    cousin_degree = min(up1, up2) - 1
    removed = abs(up1 - up2)
    return f"{_ordinal(cousin_degree)} cousin{_removed_phrase(removed)}"


def name_relationship(tree: FamilyTree, g: nx.DiGraph, id1: str, id2: str) -> str | None:
    """
    Return a human relationship term describing how id2 relates to id1
    (e.g. "grandmother", "first cousin, once removed", "sister-in-law"),
    or None if no supported pattern matches -- callers should fall back
    to the raw chain in that case rather than guessing.
    """
    if id1 == id2:
        return None

    sex2 = tree.get_individual(id2).sex

    if id2 in _spouses(g, id1):
        return _gendered(sex2, "husband", "wife", "spouse")

    blood = _blood_relationship(tree, g, id1, id2)
    if blood is not None:
        return blood

    # id2 is a sibling or parent of id1's spouse
    for spouse_id in _spouses(g, id1):
        rel = _blood_relationship(tree, g, spouse_id, id2)
        if rel in ("brother", "sister", "sibling"):
            return _gendered(sex2, "brother-in-law", "sister-in-law", "sibling-in-law")
        if rel in ("father", "mother", "parent"):
            return _gendered(sex2, "father-in-law", "mother-in-law", "parent-in-law")

    # id2 is the spouse of id1's sibling or child
    for spouse_id in _spouses(g, id2):
        rel = _blood_relationship(tree, g, id1, spouse_id)
        if rel in ("brother", "sister", "sibling"):
            return _gendered(sex2, "brother-in-law", "sister-in-law", "sibling-in-law")
        if rel in ("son", "daughter", "child"):
            return _gendered(sex2, "son-in-law", "daughter-in-law", "child-in-law")

    return None
