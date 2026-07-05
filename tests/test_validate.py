from pathlib import Path

import pytest

from gedcomtoolkit.graph import build_graph
from gedcomtoolkit.parser import parse_gedcom
from gedcomtoolkit.validate import run_validation

BROKEN_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "broken.ged"


@pytest.fixture
def broken_issues():
    tree = parse_gedcom(BROKEN_GEDCOM)
    g = build_graph(tree)
    return run_validation(tree, g)


def _messages(issues, category):
    return [i.message for i in issues if i.category == category]


def test_clean_tree_only_flags_the_expected_gap(sample_tree):
    """sample.ged has one genuine gap: Mary Jones (b.1902) has no death date
    recorded, so she'd be implausibly old today -- the validator is right to
    flag that. Nothing else in this small fixture should trip any rule."""
    g = build_graph(sample_tree)
    issues = run_validation(sample_tree, g)
    assert len(issues) == 1
    assert issues[0].category == "implausible_age"
    assert "Mary Jones" in issues[0].message


def test_detects_cycle(broken_issues):
    cycle_issues = _messages(broken_issues, "cycle")
    assert len(cycle_issues) == 1
    assert "Loop" in cycle_issues[0]


def test_detects_death_before_birth(broken_issues):
    issues = _messages(broken_issues, "death_before_birth")
    assert len(issues) == 1
    assert "Ghost Person" in issues[0]


def test_detects_implausible_age_at_death(broken_issues):
    issues = _messages(broken_issues, "implausible_age")
    assert any("Anna Old" in msg and "150 years" in msg for msg in issues)


def test_detects_parent_too_young(broken_issues):
    issues = _messages(broken_issues, "parent_child_timing")
    assert any("Teen Parent" in msg and "5 years old" in msg for msg in issues)


def test_detects_posthumous_birth(broken_issues):
    issues = _messages(broken_issues, "parent_child_timing")
    assert any("Late Child" in msg and "after" in msg and "Dead Parent" in msg for msg in issues)


def test_total_issue_count_on_broken_fixture(broken_issues):
    # 1 cycle + 1 death-before-birth + 1 implausible age + 2 parent/child timing
    assert len(broken_issues) == 5
