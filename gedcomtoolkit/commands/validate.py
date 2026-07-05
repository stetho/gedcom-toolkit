from __future__ import annotations

import sys

import click
from rich.console import Console
from rich.table import Table

from gedcomtoolkit.graph import build_graph
from gedcomtoolkit.parser import parse_gedcom
from gedcomtoolkit.validate import CATEGORIES, run_validation

SEVERITY_STYLE = {"error": "bold red", "warning": "yellow"}


@click.command()
@click.argument("gedcom_file", type=click.Path(exists=True))
@click.option(
    "--ignore",
    "ignored_categories",
    multiple=True,
    type=click.Choice(CATEGORIES),
    help="Exclude a category of issue from the report. Repeatable, "
    "e.g. --ignore implausible_age --ignore cycle.",
)
def command(gedcom_file: str, ignored_categories: tuple[str, ...]):
    """Check a GEDCOM file for data problems (cycles, impossible dates, implausible ages)."""
    tree = parse_gedcom(gedcom_file)
    g = build_graph(tree)
    issues = run_validation(tree, g)

    if ignored_categories:
        issues = [i for i in issues if i.category not in ignored_categories]

    console = Console()

    if not issues:
        console.print(f"[bold green]No issues found[/bold green] in {gedcom_file}")
        return

    table = Table(title=f"Validation issues in {gedcom_file}")
    table.add_column("Severity")
    table.add_column("Category")
    table.add_column("Details")

    error_count = 0
    for issue in issues:
        style = SEVERITY_STYLE.get(issue.severity, "")
        table.add_row(f"[{style}]{issue.severity}[/{style}]", issue.category, issue.message)
        if issue.severity == "error":
            error_count += 1

    console.print(table)
    warning_count = len(issues) - error_count
    console.print(f"\n{len(issues)} issue(s): {error_count} error(s), {warning_count} warning(s)")

    if error_count:
        sys.exit(1)
