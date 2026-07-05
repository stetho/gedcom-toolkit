from pathlib import Path

from click.testing import CliRunner

from gedcomtoolkit.cli import cli

SAMPLE_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "sample.ged"


def test_stats_command_runs_successfully():
    runner = CliRunner()
    result = runner.invoke(cli, ["stats", str(SAMPLE_GEDCOM)])
    assert result.exit_code == 0
    assert "Individuals" in result.output
    assert "5" in result.output


def test_stats_command_missing_file_errors():
    runner = CliRunner()
    result = runner.invoke(cli, ["stats", "does_not_exist.ged"])
    assert result.exit_code != 0
