from __future__ import annotations

import sys

import click
from rich.console import Console
from rich.table import Table

from gedcomtoolkit.graph import build_graph
from gedcomtoolkit.parser import parse_gedcom
from gedcomtoolkit.relationship import (
    AmbiguousPersonError,
    PersonNotFoundError,
    describe_relationship_path,
    resolve_person,
)
from gedcomtoolkit.relationship_naming import name_relationship


def _print_ambiguous(console: Console, err: AmbiguousPersonError) -> None:
    console.print(
        f"[yellow]'{err.query}' matches more than one person -- "
        "re-run with a specific ID:[/yellow]"
    )
    table = Table()
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Born")
    for indi in err.candidates:
        table.add_row(indi.xref_id, indi.full_name, indi.birth_date or "?")
    console.print(table)


@click.command()
@click.argument("gedcom_file", type=click.Path(exists=True))
@click.argument("person1")
@click.argument("person2")
def command(gedcom_file: str, person1: str, person2: str):
    """Find the relationship path between two individuals.

    PERSON1 and PERSON2 can each be a name or an xref_id (e.g. @I123@).
    If a name matches more than one individual, every match is shown --
    use gedcom findid to look up the right one, then re-run with its ID.
    """
    tree = parse_gedcom(gedcom_file)
    g = build_graph(tree)
    console = Console()

    try:
        indi1 = resolve_person(tree, person1)
        indi2 = resolve_person(tree, person2)
    except AmbiguousPersonError as e:
        _print_ambiguous(console, e)
        sys.exit(1)
    except PersonNotFoundError as e:
        console.print(f"[red]No individual found matching '{e}'[/red]")
        sys.exit(1)

    if indi1.xref_id == indi2.xref_id:
        console.print(f"{indi1.full_name} is the same person.")
        return

    steps = describe_relationship_path(tree, g, indi1.xref_id, indi2.xref_id)

    if steps is None:
        console.print(
            f"[yellow]No relationship path found between {indi1.full_name} and "
            f"{indi2.full_name} -- they may be in disconnected parts of the tree.[/yellow]"
        )
        sys.exit(1)

    console.print(f"[bold]{indi1.full_name}[/bold]")
    for _from_name, label, to_name in steps:
        console.print(f"  {label} [bold]{to_name}[/bold]")

    relationship_name = name_relationship(tree, g, indi1.xref_id, indi2.xref_id)
    if relationship_name:
        console.print(f"\n{indi2.full_name} is {indi1.full_name}'s {relationship_name}.")
    else:
        console.print(
            "\nNo simple relationship term for this connection -- "
            "see the chain above."
        )
