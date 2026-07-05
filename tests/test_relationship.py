from pathlib import Path

import pytest

from gedcomtoolkit.graph import build_graph
from gedcomtoolkit.parser import parse_gedcom
from gedcomtoolkit.relationship import (
    AmbiguousPersonError,
    PersonNotFoundError,
    describe_relationship_path,
    resolve_person,
)

AMBIGUOUS_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "ambiguous.ged"
BROKEN_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "broken.ged"


# --- resolve_person -----------------------------------------------------


def test_resolve_by_xref_id(sample_tree):
    indi = resolve_person(sample_tree, "@I1@")
    assert indi.full_name == "John Smith"


def test_resolve_unknown_xref_id_raises(sample_tree):
    with pytest.raises(PersonNotFoundError):
        resolve_person(sample_tree, "@I999@")


def test_resolve_unique_name(sample_tree):
    indi = resolve_person(sample_tree, "Bob Brown")
    assert indi.xref_id == "@I4@"


def test_resolve_unknown_name_raises(sample_tree):
    with pytest.raises(PersonNotFoundError):
        resolve_person(sample_tree, "Nobody Here")


def test_resolve_ambiguous_name_raises_with_candidates():
    tree = parse_gedcom(AMBIGUOUS_GEDCOM)
    with pytest.raises(AmbiguousPersonError) as exc_info:
        resolve_person(tree, "Bob Smith")
    assert len(exc_info.value.candidates) == 3


# --- describe_relationship_path -----------------------------------------
# sample.ged: John Smith(@I1@) + Mary Jones(@I2@) -> Alice Smith(@I3@)
#             Alice Smith(@I3@) + Bob Brown(@I4@) -> Carol Brown(@I5@)


def test_grandparent_to_grandchild_chain(sample_tree):
    g = build_graph(sample_tree)
    steps = describe_relationship_path(sample_tree, g, "@I1@", "@I5@")
    labels = [label for _f, label, _t in steps]
    names = [to for _f, _l, to in steps]
    assert labels == ["parent of", "parent of"]
    assert names == ["Alice Smith", "Carol Brown"]


def test_reverse_direction_uses_child_of(sample_tree):
    g = build_graph(sample_tree)
    steps = describe_relationship_path(sample_tree, g, "@I5@", "@I1@")
    labels = [label for _f, label, _t in steps]
    names = [to for _f, _l, to in steps]
    assert labels == ["child of", "child of"]
    assert names == ["Alice Smith", "John Smith"]


def test_spouse_edge_in_path(sample_tree):
    g = build_graph(sample_tree)
    # Bob Brown (@I4@, married in) to Mary Jones (@I2@): spouse -> child of
    steps = describe_relationship_path(sample_tree, g, "@I4@", "@I2@")
    labels = [label for _f, label, _t in steps]
    assert labels == ["spouse of", "child of"]


def test_no_path_between_disconnected_individuals():
    tree = parse_gedcom(BROKEN_GEDCOM)
    g = build_graph(tree)
    # @I1@ (Anna Old) has no family links at all in broken.ged
    steps = describe_relationship_path(tree, g, "@I1@", "@I4@")
    assert steps is None
