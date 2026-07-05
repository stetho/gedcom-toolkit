from pathlib import Path

import pytest

from gedcomtoolkit.graph import build_graph
from gedcomtoolkit.parser import parse_gedcom
from gedcomtoolkit.relationship_naming import name_relationship

EXTENDED_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "extended.ged"

# Fixture map, for readability in the assertions below:
# @I1@  Greatgrand One   (M)  ─┐
# @I2@  Greatgrand Two   (F)  ─┴─ @I3@ Grand One (M)
# @I3@ Grand One (M) + @I4@ Grand Two (F) -> @I5@ Parent One (M), @I6@ Parent Two (F)  [siblings]
# @I5@ Parent One (M) + @I7@ Parentonespouse Married (F) -> @I9@  Cousin One (M)
# @I6@ Parent Two (F) + @I8@ Parenttwospouse Married (M) -> @I10@ Cousin Two (F)
# @I9@ Cousin One (M) -> @I11@ Greatgrandchild One (F)


@pytest.fixture
def tree_and_graph():
    tree = parse_gedcom(EXTENDED_GEDCOM)
    g = build_graph(tree)
    return tree, g


def _name(tree, g, id1, id2):
    return name_relationship(tree, g, id1, id2)


# --- lineal ---------------------------------------------------------------


def test_parent_and_child(tree_and_graph):
    tree, g = tree_and_graph
    assert _name(tree, g, "@I3@", "@I5@") == "son"
    assert _name(tree, g, "@I5@", "@I3@") == "father"


def test_grandparent_and_grandchild(tree_and_graph):
    tree, g = tree_and_graph
    assert _name(tree, g, "@I1@", "@I5@") == "grandson"
    assert _name(tree, g, "@I5@", "@I1@") == "grandfather"


def test_great_grandparent_and_great_grandchild(tree_and_graph):
    tree, g = tree_and_graph
    assert _name(tree, g, "@I1@", "@I9@") == "great-grandson"
    assert _name(tree, g, "@I9@", "@I1@") == "great-grandfather"


def test_great_great_grandparent(tree_and_graph):
    tree, g = tree_and_graph
    assert _name(tree, g, "@I1@", "@I11@") == "great-great-granddaughter"
    assert _name(tree, g, "@I11@", "@I1@") == "great-great-grandfather"


# --- siblings ---------------------------------------------------------------


def test_siblings(tree_and_graph):
    tree, g = tree_and_graph
    assert _name(tree, g, "@I5@", "@I6@") == "sister"
    assert _name(tree, g, "@I6@", "@I5@") == "brother"


# --- aunt/uncle and niece/nephew --------------------------------------------


def test_aunt_and_nephew(tree_and_graph):
    tree, g = tree_and_graph
    # @I6@ (Parent Two, F) is @I9@'s (Cousin One, M) aunt
    assert _name(tree, g, "@I9@", "@I6@") == "aunt"
    assert _name(tree, g, "@I6@", "@I9@") == "nephew"


def test_uncle_and_niece(tree_and_graph):
    tree, g = tree_and_graph
    # @I5@ (Parent One, M) is @I10@'s (Cousin Two, F) uncle
    assert _name(tree, g, "@I10@", "@I5@") == "uncle"
    assert _name(tree, g, "@I5@", "@I10@") == "niece"


def test_great_aunt_and_great_niece(tree_and_graph):
    tree, g = tree_and_graph
    # @I6@ is sibling of @I11@'s grandparent (@I5@) -> great-aunt / great-niece
    assert _name(tree, g, "@I11@", "@I6@") == "great-aunt"
    assert _name(tree, g, "@I6@", "@I11@") == "great-niece"


# --- cousins ------------------------------------------------------------


def test_first_cousins(tree_and_graph):
    tree, g = tree_and_graph
    assert _name(tree, g, "@I9@", "@I10@") == "first cousin"
    assert _name(tree, g, "@I10@", "@I9@") == "first cousin"


def test_first_cousin_once_removed(tree_and_graph):
    tree, g = tree_and_graph
    assert _name(tree, g, "@I10@", "@I11@") == "first cousin, once removed"
    assert _name(tree, g, "@I11@", "@I10@") == "first cousin, once removed"


# --- spouse and in-laws ---------------------------------------------------


def test_direct_spouse(tree_and_graph):
    tree, g = tree_and_graph
    assert _name(tree, g, "@I5@", "@I7@") == "wife"
    assert _name(tree, g, "@I7@", "@I5@") == "husband"


def test_sibling_in_law_via_spouses_sibling(tree_and_graph):
    tree, g = tree_and_graph
    # @I7@ (Parent One's wife) & @I6@ (Parent One's sister)
    assert _name(tree, g, "@I7@", "@I6@") == "sister-in-law"
    assert _name(tree, g, "@I6@", "@I7@") == "sister-in-law"


def test_parent_in_law_via_spouses_parent(tree_and_graph):
    tree, g = tree_and_graph
    # @I3@ (Grand One) is @I7@'s (Parent One's wife) father-in-law
    assert _name(tree, g, "@I3@", "@I7@") == "daughter-in-law"
    assert _name(tree, g, "@I7@", "@I3@") == "father-in-law"


# --- honest fallback -------------------------------------------------------


def test_no_term_for_distant_in_law(tree_and_graph):
    tree, g = tree_and_graph
    # @I1@ (great-grandparent) has no supported relationship to @I7@
    # (their grandchild's spouse) -- should honestly return None
    assert _name(tree, g, "@I1@", "@I7@") is None


def test_same_person_returns_none(tree_and_graph):
    tree, g = tree_and_graph
    assert _name(tree, g, "@I5@", "@I5@") is None
