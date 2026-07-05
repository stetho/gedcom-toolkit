from pathlib import Path

from click.testing import CliRunner

from gedcomtoolkit.cli import cli

AMBIGUOUS_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "ambiguous.ged"
BROKEN_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "broken.ged"
SAMPLE_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "sample.ged"


def test_findrelationship_by_name():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["findrelationship", str(SAMPLE_GEDCOM), "John Smith", "Carol Brown"]
    )
    assert result.exit_code == 0
    assert "John Smith" in result.output
    assert "parent of" in result.output
    assert "Carol Brown" in result.output


def test_findrelationship_by_xref_id():
    runner = CliRunner()
    result = runner.invoke(cli, ["findrelationship", str(SAMPLE_GEDCOM), "@I1@", "@I5@"])
    assert result.exit_code == 0
    assert "Carol Brown" in result.output


def test_findrelationship_same_person():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["findrelationship", str(SAMPLE_GEDCOM), "@I1@", "John Smith"]
    )
    assert result.exit_code == 0
    assert "same person" in result.output


def test_findrelationship_ambiguous_name_shows_candidates():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["findrelationship", str(AMBIGUOUS_GEDCOM), "Bob Smith", "Alice"]
    )
    assert result.exit_code == 1
    assert "@I1@" in result.output
    assert "@I2@" in result.output
    assert "@I3@" in result.output


def test_findrelationship_unknown_name():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["findrelationship", str(SAMPLE_GEDCOM), "Nobody Here", "John Smith"]
    )
    assert result.exit_code == 1
    assert "No individual found" in result.output


def test_findrelationship_no_path():
    runner = CliRunner()
    result = runner.invoke(cli, ["findrelationship", str(BROKEN_GEDCOM), "@I1@", "@I4@"])
    assert result.exit_code == 1
    assert "No relationship path found" in result.output
