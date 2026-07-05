from __future__ import annotations

import sys

import click
from rich.console import Console
from rich.table import Table

from gedcomtoolkit.parser import parse_gedcom
from gedcomtoolkit.search import find_individuals_by_name


@click.command()
@click.argument("gedcom_file", type=click.Path(exists=True))
@click.argument("name")
def command(gedcom_file: str, name: str):
    """Find individuals by name and print their unique xref_id.

    GEDCOM names aren't unique -- a great-grandfather, his father, and a
    couple of distant cousins can easily share the same name. This prints
    every match with its xref_id, so you can pick the right one to pass to
    commands that need an unambiguous individual (e.g. gedcom findrelationship,
    once it exists).
    """
    tree = parse_gedcom(gedcom_file)
    matches = find_individuals_by_name(tree, name)

    console = Console()

    if not matches:
        console.print(f"[yellow]No individuals found matching '{name}'[/yellow]")
        sys.exit(1)

    table = Table(title=f"Matches for '{name}'")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Born")
    table.add_column("Died")

    for indi in matches:
        died = indi.death_date or ("" if indi.is_living else "?")
        table.add_row(indi.xref_id, indi.full_name, indi.birth_date or "?", died)

    console.print(table)

    if len(matches) > 1:
        console.print(
            f"\n{len(matches)} matches -- use the ID with commands that need "
            "a specific individual."
        )
