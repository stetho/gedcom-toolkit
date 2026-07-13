from pathlib import Path

from click.testing import CliRunner

from gedcomtoolkit.cli import cli

DUPLICATES_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "duplicates.ged"


def test_duplicates_shows_candidates():
    runner = CliRunner()
    result = runner.invoke(cli, ["duplicates", str(DUPLICATES_GEDCOM)])
    assert result.exit_code == 0
    assert "Someone Duplicate" in result.output
    assert "90%" in result.output


def test_duplicates_excludes_far_apart():
    runner = CliRunner()
    result = runner.invoke(cli, ["duplicates", str(DUPLICATES_GEDCOM)])
    assert "Far Apart" not in result.output


def test_duplicates_namesake_note_shown():
    runner = CliRunner()
    result = runner.invoke(cli, ["duplicates", str(DUPLICATES_GEDCOM)])
    assert "namesake" in result.output.lower()
