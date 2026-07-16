from pathlib import Path

from click.testing import CliRunner

from gedcomtoolkit.cli import cli

COMPLETENESS_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "completeness.ged"
BROKEN_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "broken.ged"


def test_completeness_shows_all_generations():
    runner = CliRunner()
    result = runner.invoke(cli, ["completeness", str(COMPLETENESS_GEDCOM)])
    assert result.exit_code == 0
    assert "50%" in result.output  # gen1/gen2 both/one split


def test_completeness_errors_on_cyclic_tree():
    runner = CliRunner()
    result = runner.invoke(cli, ["completeness", str(BROKEN_GEDCOM)])
    assert result.exit_code == 1
    assert "cycle" in result.output.lower()
    assert "gedcom validate" in result.output.lower()
