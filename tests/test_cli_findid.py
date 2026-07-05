from pathlib import Path

from click.testing import CliRunner

from gedcomtoolkit.cli import cli

AMBIGUOUS_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "ambiguous.ged"
SAMPLE_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "sample.ged"


def test_findid_shows_all_ambiguous_matches():
    runner = CliRunner()
    result = runner.invoke(cli, ["findid", str(AMBIGUOUS_GEDCOM), "Bob Smith"])
    assert result.exit_code == 0
    assert "@I1@" in result.output
    assert "@I2@" in result.output
    assert "@I3@" in result.output
    assert "3 matches" in result.output


def test_findid_single_match_no_count_message():
    runner = CliRunner()
    result = runner.invoke(cli, ["findid", str(AMBIGUOUS_GEDCOM), "Alice"])
    assert result.exit_code == 0
    assert "@I4@" in result.output
    assert "matches --" not in result.output


def test_findid_no_match_exits_nonzero():
    runner = CliRunner()
    result = runner.invoke(cli, ["findid", str(SAMPLE_GEDCOM), "Nobody Here"])
    assert result.exit_code == 1
    assert "No individuals found" in result.output
