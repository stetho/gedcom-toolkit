from pathlib import Path

import pytest

from gedcomtoolkit.completeness import (
    CyclicTreeError,
    compute_completeness,
    compute_generations,
)
from gedcomtoolkit.graph import build_graph
from gedcomtoolkit.parser import parse_gedcom

COMPLETENESS_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "completeness.ged"

# completeness.ged:
#
# Generation 0 (no known parents -- structurally guaranteed):
#   @I1@ Root A1, @I2@ Root A2, @I3@ Root A3, @I4@ Root A4 (isolate),
#   @I5@ Married InSpouse (marries in, no parents of her own)
#   -> total 5, all "no parents"
#
# Generation 1:
#   @I6@ Gen1 Both  (FAMC @F1@: HUSB @I1@ + WIFE @I2@ -> both parents)
#     generation = 1 + max(gen(@I1@)=0, gen(@I2@)=0) = 1
#   @I7@ Gen1 One   (FAMC @F2@: HUSB @I3@ only -> one parent)
#     generation = 1 + gen(@I3@)=0 = 1
#   -> total 2, both_parents=1, one_parent=1
#
# Generation 2:
#   @I8@ Gen2 Both  (FAMC @F3@: HUSB @I6@(gen1) + WIFE @I5@(gen0) -> both parents)
#     generation = 1 + max(gen(@I6@)=1, gen(@I5@)=0) = 2
#   @I9@ Gen2 One   (FAMC @F4@: HUSB @I7@(gen1) only -> one parent)
#     generation = 1 + gen(@I7@)=1 = 2
#   -> total 2, both_parents=1, one_parent=1


@pytest.fixture
def tree_and_graph():
    tree = parse_gedcom(COMPLETENESS_GEDCOM)
    g = build_graph(tree)
    return tree, g


def test_generation_numbers(tree_and_graph):
    tree, g = tree_and_graph
    generations = compute_generations(g)

    for xref_id in ("@I1@", "@I2@", "@I3@", "@I4@", "@I5@"):
        assert generations[xref_id] == 0

    assert generations["@I6@"] == 1
    assert generations["@I7@"] == 1
    assert generations["@I8@"] == 2
    assert generations["@I9@"] == 2


def test_generation_0_is_always_all_no_parents(tree_and_graph):
    tree, g = tree_and_graph
    rows = compute_completeness(tree, g)
    gen0 = next(r for r in rows if r.generation == 0)

    assert gen0.total == 5
    assert gen0.no_parents == 5
    assert gen0.both_parents == 0
    assert gen0.one_parent == 0
    assert gen0.none_pct == 100.0


def test_generation_1_breakdown(tree_and_graph):
    tree, g = tree_and_graph
    rows = compute_completeness(tree, g)
    gen1 = next(r for r in rows if r.generation == 1)

    assert gen1.total == 2
    assert gen1.both_parents == 1
    assert gen1.one_parent == 1
    assert gen1.no_parents == 0
    assert gen1.both_pct == 50.0
    assert gen1.one_pct == 50.0


def test_generation_2_breakdown(tree_and_graph):
    tree, g = tree_and_graph
    rows = compute_completeness(tree, g)
    gen2 = next(r for r in rows if r.generation == 2)

    assert gen2.total == 2
    assert gen2.both_parents == 1
    assert gen2.one_parent == 1


def test_rows_sorted_by_generation(tree_and_graph):
    tree, g = tree_and_graph
    rows = compute_completeness(tree, g)
    assert [r.generation for r in rows] == [0, 1, 2]


def test_cyclic_tree_raises():
    broken_tree = parse_gedcom(Path(__file__).parent.parent / "data" / "sample" / "broken.ged")
    broken_g = build_graph(broken_tree)

    with pytest.raises(CyclicTreeError):
        compute_generations(broken_g)
