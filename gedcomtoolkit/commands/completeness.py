from __future__ import annotations

import sys

import click
from rich.console import Console
from rich.table import Table

from gedcomtoolkit.completeness import CyclicTreeError, compute_completeness
from gedcomtoolkit.graph import build_graph
from gedcomtoolkit.parser import parse_gedcom


@click.command()
@click.argument("gedcom_file", type=click.Path(exists=True))
def command(gedcom_file: str):
    """Report parent-linkage completeness, broken down by generation.

    "Generation" means depth from the nearest known root in each
    individual's own line, not absolute chronological era -- someone with
    zero known parents is generation 0 for this report even if they're
    not the file's oldest person, they just haven't had a parent
    researched yet. Requires an acyclic tree; run `gedcom validate` first
    if that hasn't been confirmed recently.
    """
    tree = parse_gedcom(gedcom_file)
    g = build_graph(tree)

    try:
        rows = compute_completeness(tree, g)
    except CyclicTreeError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    console = Console()
    table = Table(title=f"Parent-linkage completeness in {gedcom_file}")
    table.add_column("Generation", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Both parents", justify="right")
    table.add_column("One parent", justify="right")
    table.add_column("No parents", justify="right")

    for row in rows:
        table.add_row(
            str(row.generation),
            str(row.total),
            f"{row.both_parents} ({row.both_pct:.0f}%)",
            f"{row.one_parent} ({row.one_pct:.0f}%)",
            f"{row.no_parents} ({row.none_pct:.0f}%)",
        )

    console.print(table)
    console.print(
        "\n[dim]Generation 0 = no known parents in this file (a genuine root "
        "ancestor, or simply an unresearched gap) -- always 100% \"no parents\" "
        "by definition, not a finding.[/dim]"
    )
