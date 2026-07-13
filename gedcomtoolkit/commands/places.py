from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from gedcomtoolkit.parser import parse_gedcom
from gedcomtoolkit.places import find_place_suggestions


@click.command()
@click.argument("gedcom_file", type=click.Path(exists=True))
def command(gedcom_file: str):
    """Suggest normalised forms for place-name variants.

    Groups place strings by their primary place name (e.g. "Croydon") and
    suggests a canonical form for each group, with a confidence score.
    Dry-run report only -- never rewrites the file. Some variants reflect
    genuine historical differences (a place moving between counties, say)
    rather than messy data, so those are shown separately as conflicts
    rather than silently merged.
    """
    tree = parse_gedcom(gedcom_file)
    suggestions = find_place_suggestions(tree)

    console = Console()

    if not suggestions:
        console.print("[bold green]No place-name variants found[/bold green] to normalise.")
        return

    for suggestion in suggestions:
        title = f'"{suggestion.primary_key.title()}" -> suggested: "{suggestion.suggested_canonical}"'
        table = Table(title=title)
        table.add_column("Variant")
        table.add_column("Count", justify="right")
        table.add_column("Status")

        for display, count in suggestion.compatible_variants:
            table.add_row(display, str(count), "[green]compatible[/green]")
        for display, count in suggestion.conflicting_variants:
            table.add_row(display, str(count), "[yellow]conflict -- review manually[/yellow]")

        console.print(table)

        total_compatible = sum(count for _d, count in suggestion.compatible_variants)
        console.print(
            f"Confidence: {suggestion.confidence:.0f}%  "
            f"(this exact form appears {suggestion.canonical_count} time(s) in the file)"
        )
        if suggestion.canonical_count < total_compatible:
            console.print(
                "[dim]Note: the suggested form is used less often than the variants "
                "it's replacing -- worth checking it isn't itself a one-off typo "
                "before applying it.[/dim]"
            )
        console.print()
