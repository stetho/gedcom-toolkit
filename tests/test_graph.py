import networkx as nx

from gedcomtoolkit.graph import build_graph


def test_node_count_matches_individuals(sample_tree):
    g = build_graph(sample_tree)
    assert g.number_of_nodes() == len(sample_tree.individuals)


def test_parent_child_edges_exist(sample_tree):
    g = build_graph(sample_tree)
    assert g.has_edge("@I1@", "@I3@")  # John -> Alice
    assert g.get_edge_data("@I1@", "@I3@")["relation"] == "parent"


def test_spouse_edges_are_bidirectional(sample_tree):
    g = build_graph(sample_tree)
    assert g.has_edge("@I1@", "@I2@")
    assert g.has_edge("@I2@", "@I1@")
    assert g.get_edge_data("@I1@", "@I2@")["relation"] == "spouse"


def test_descendants_of_root_ancestor(sample_tree):
    g = build_graph(sample_tree)
    # John (@I1@) should reach Alice (@I3@) and Carol (@I5@) via parent edges
    parent_only = nx.DiGraph(
        (u, v) for u, v, d in g.edges(data=True) if d["relation"] == "parent"
    )
    descendants = nx.descendants(parent_only, "@I1@")
    assert descendants == {"@I3@", "@I5@"}


def test_whole_tree_is_one_component(sample_tree):
    g = build_graph(sample_tree)
    assert nx.number_weakly_connected_components(g) == 1
