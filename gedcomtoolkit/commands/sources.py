from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from gedcomtoolkit.parser import parse_gedcom
from gedcomtoolkit.sources import (
    compute_source_stats,
    find_unsourced_individuals,
    find_unsourced_marriages,
)


def _pct(rate: float | None) -> str:
    return "n/a" if rate is None else f"{rate:.0f}%"


@click.command()
@click.argument("gedcom_file", type=click.Path(exists=True))
@click.option(
    "--limit",
    default=20,
    show_default=True,
    help="Maximum number of unsourced individuals/marriages to list.",
)
def command(gedcom_file: str, limit: int):
    """Report how well-evidenced a tree is, not just how complete it is.

    Measures source-citation coverage on events that have a date recorded
    (an undated event can't meaningfully be "unsourced"), then lists the
    individuals and marriages with the most unsourced facts.
    """
    tree = parse_gedcom(gedcom_file)
    stats = compute_source_stats(tree)

    console = Console()

    summary = Table(title=f"Source coverage in {gedcom_file}")
    summary.add_column("Event")
    summary.add_column("Recorded", justify="right")
    summary.add_column("Sourced", justify="right")
    summary.add_column("Rate", justify="right")

    summary.add_row(
        "Births", str(stats.births_recorded), str(stats.births_sourced), _pct(stats.birth_source_rate)
    )
    summary.add_row(
        "Deaths", str(stats.deaths_recorded), str(stats.deaths_sourced), _pct(stats.death_source_rate)
    )
    summary.add_row(
        "Marriages",
        str(stats.marriages_recorded),
        str(stats.marriages_sourced),
        _pct(stats.marriage_source_rate),
    )
    summary.add_row(
        "Overall",
        str(stats.births_recorded + stats.deaths_recorded + stats.marriages_recorded),
        str(stats.births_sourced + stats.deaths_sourced + stats.marriages_sourced),
        _pct(stats.overall_source_rate),
        style="bold",
    )

    console.print(summary)

    unsourced_individuals = find_unsourced_individuals(tree)
    if unsourced_individuals:
        console.print()
        indi_table = Table(title="Individuals with unsourced facts")
        indi_table.add_column("Name")
        indi_table.add_column("ID")
        indi_table.add_column("Unsourced facts")

        for record in unsourced_individuals[:limit]:
            indi_table.add_row(
                record.individual.full_name,
                record.individual.xref_id,
                ", ".join(record.unsourced_facts),
            )
        console.print(indi_table)

        if len(unsourced_individuals) > limit:
            console.print(f"...and {len(unsourced_individuals) - limit} more.")

    unsourced_marriages = find_unsourced_marriages(tree)
    if unsourced_marriages:
        console.print()
        marr_table = Table(title="Unsourced marriages")
        marr_table.add_column("Spouses")
        marr_table.add_column("ID")
        marr_table.add_column("Date")

        for record in unsourced_marriages[:limit]:
            marr_table.add_row(record.spouse_names, record.xref_id, record.marriage_date)
        console.print(marr_table)

        if len(unsourced_marriages) > limit:
            console.print(f"...and {len(unsourced_marriages) - limit} more.")
