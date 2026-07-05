from pathlib import Path

from click.testing import CliRunner

from gedcomtoolkit.cli import cli

BROKEN_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "broken.ged"
SAMPLE_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "sample.ged"


def test_validate_reports_all_issues_by_default():
    runner = CliRunner()
    result = runner.invoke(cli, ["validate", str(BROKEN_GEDCOM)])
    assert result.exit_code == 1  # errors present
    assert "5 issue(s): 4 error(s), 1 warning(s)" in result.output


def test_validate_clean_ish_file_exits_zero():
    runner = CliRunner()
    result = runner.invoke(cli, ["validate", str(SAMPLE_GEDCOM)])
    assert result.exit_code == 0  # warnings only, no errors


def test_ignore_flag_filters_category():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["validate", str(BROKEN_GEDCOM), "--ignore", "implausible_age"]
    )
    assert "implausible_age" not in result.output
    assert "cycle" in result.output  # other categories still shown
    assert "4 issue(s): 4 error(s), 0 warning(s)" in result.output


def test_ignore_flag_repeatable():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "validate",
            str(BROKEN_GEDCOM),
            "--ignore",
            "implausible_age",
            "--ignore",
            "cycle",
        ],
    )
    assert "implausible_age" not in result.output
    assert "cycle" not in result.output
    assert "3 issue(s): 3 error(s), 0 warning(s)" in result.output


def test_ignore_flag_rejects_unknown_category():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["validate", str(BROKEN_GEDCOM), "--ignore", "not_a_real_category"]
    )
    assert result.exit_code != 0
    assert "Invalid value" in result.output
