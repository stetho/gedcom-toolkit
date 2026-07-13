from pathlib import Path

from click.testing import CliRunner

from gedcomtoolkit.cli import cli

PLACES_GEDCOM = Path(__file__).parent.parent / "data" / "sample" / "places.ged"


def test_places_shows_croydon_suggestion():
    runner = CliRunner()
    result = runner.invoke(cli, ["places", str(PLACES_GEDCOM)])
    assert result.exit_code == 0
    assert "Croydon" in result.output
    assert "Croydon, Surrey, England" in result.output
    assert "67%" in result.output or "66%" in result.output


def test_places_flags_conflict():
    runner = CliRunner()
    result = runner.invoke(cli, ["places", str(PLACES_GEDCOM)])
    assert "Greater London" in result.output
    assert "conflict" in result.output.lower()


def test_places_excludes_single_variant_place():
    runner = CliRunner()
    result = runner.invoke(cli, ["places", str(PLACES_GEDCOM)])
    assert "Brighton" not in result.output


def test_places_warns_when_canonical_is_rarer_than_components():
    runner = CliRunner()
    result = runner.invoke(cli, ["places", str(PLACES_GEDCOM)])
    # Croydon's suggested canonical is used only once, vs 8 uses of its components
    assert "appears 1 time(s)" in result.output
    assert "worth checking" in result.output.lower()
