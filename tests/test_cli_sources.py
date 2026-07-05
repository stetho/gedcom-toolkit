from pathlib import Path

from click.testing import CliRunner

from gedcomtoolkit.cli import cli

SOURCES_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "sources.ged"


def test_sources_summary():
    runner = CliRunner()
    result = runner.invoke(cli, ["sources", str(SOURCES_GEDCOM)])
    assert result.exit_code == 0
    assert "Births" in result.output
    assert "50%" in result.output


def test_sources_lists_unsourced_individuals():
    runner = CliRunner()
    result = runner.invoke(cli, ["sources", str(SOURCES_GEDCOM)])
    assert "Test Two" in result.output
    assert "Test One" not in result.output  # fully sourced, shouldn't appear in the gap list


def test_sources_lists_unsourced_marriages():
    runner = CliRunner()
    result = runner.invoke(cli, ["sources", str(SOURCES_GEDCOM)])
    assert "Unsourced marriages" in result.output
    assert "1955" in result.output
