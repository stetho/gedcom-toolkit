from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from gedcomtoolkit.duplicates import find_duplicate_candidates
from gedcomtoolkit.parser import parse_gedcom


@click.command()
@click.argument("gedcom_file", type=click.Path(exists=True))
def command(gedcom_file: str):
    """Flag probable duplicate individuals within a single file.

    Groups individuals by exact name match, then reports the signals for
    each pair (birth-year gap, whether they share the same parents) rather
    than asserting a verdict -- same name and close birth year can also
    mean a genuine namesake sibling, not a duplicate record.
    """
    tree = parse_gedcom(gedcom_file)
    candidates = find_duplicate_candidates(tree)

    console = Console()

    if not candidates:
        console.print("[bold green]No probable duplicates found.[/bold green]")
        return

    for candidate in candidates:
        a, b = candidate.individual_a, candidate.individual_b
        if candidate.year_diff == 0:
            year_display = "same year"
        elif candidate.year_diff is not None:
            year_display = f"{candidate.year_diff} year(s) apart"
        else:
            year_display = "unknown gap"

        table = Table(title=f'"{a.full_name}"  (confidence: {candidate.confidence:.0f}%)')
        table.add_column("ID")
        table.add_column("Birth")
        table.add_column("Parents linked")

        table.add_row(a.xref_id, a.birth_date or "?", a.family_as_child or "-")
        table.add_row(b.xref_id, b.birth_date or "?", b.family_as_child or "-")

        console.print(table)
        console.print(f"[dim]{year_display}, same parents: {candidate.same_parents}[/dim]")
        console.print(f"{candidate.note}\n")
