from pathlib import Path

from click.testing import CliRunner

from gedcomtoolkit.cli import cli

RESEARCH_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "research.ged"


def test_rn_shows_ranked_candidates():
    runner = CliRunner()
    result = runner.invoke(cli, ["rn", str(RESEARCH_GEDCOM)])
    assert result.exit_code == 0
    assert "Root One" in result.output
    assert "Root Two" in result.output
    # Root One should be ranked above Root Two (higher score)
    assert result.output.index("Root One") < result.output.index("Root Two")


def test_rn_excludes_complete_records():
    runner = CliRunner()
    result = runner.invoke(cli, ["rn", str(RESEARCH_GEDCOM)])
    assert "Child One" not in result.output
    assert "Grandchild Two" not in result.output


def test_rn_limit_option():
    runner = CliRunner()
    result = runner.invoke(cli, ["rn", str(RESEARCH_GEDCOM), "--limit", "1"])
    assert result.exit_code == 0
    assert "Root One" in result.output
    assert "Root Two" not in result.output
    assert "3 more" in result.output
