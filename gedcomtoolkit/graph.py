"""
Build a networkx.DiGraph from a FamilyTree.

Edge convention: edges point from parent -> child (direction of descent).
This makes "descendants" a forward BFS and "ancestors" a reverse BFS, which
maps naturally onto networkx's built-in traversal helpers.

Spouse relationships are stored as a separate undirected-style edge
(added both ways) with relation="spouse", since marriage has no inherent
direction.
"""

from __future__ import annotations

import networkx as nx

from gedcomtoolkit.models import FamilyTree


def build_graph(tree: FamilyTree) -> nx.DiGraph:
    g = nx.DiGraph()

    for indi in tree.individuals.values():
        g.add_node(
            indi.xref_id,
            full_name=indi.full_name,
            sex=indi.sex,
            birth_date=indi.birth_date,
            death_date=indi.death_date,
        )

    for fam in tree.families.values():
        parents = [p for p in (fam.husband_id, fam.wife_id) if p]

        for parent_id in parents:
            for child_id in fam.child_ids:
                if parent_id in g and child_id in g:
                    g.add_edge(parent_id, child_id, relation="parent")

        if fam.husband_id and fam.wife_id:
            if fam.husband_id in g and fam.wife_id in g:
                g.add_edge(fam.husband_id, fam.wife_id, relation="spouse")
                g.add_edge(fam.wife_id, fam.husband_id, relation="spouse")

    return g
