from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from gedcomtoolkit.graph import build_graph
from gedcomtoolkit.parser import parse_gedcom
from gedcomtoolkit.research import find_research_candidates


@click.command()
@click.argument("gedcom_file", type=click.Path(exists=True))
@click.option(
    "--limit",
    default=20,
    show_default=True,
    help="Maximum number of candidates to show.",
)
def command(gedcom_file: str, limit: int):
    """Suggest who to research next.

    Ranks individuals by missing data (no birth date, no death date when
    they'd clearly be deceased by now, no parents linked), weighted by how
    many descendants that gap affects -- filling in a brick wall for
    someone with many descendants is worth more than for a childless leaf.
    """
    tree = parse_gedcom(gedcom_file)
    g = build_graph(tree)
    candidates = find_research_candidates(tree, g)

    console = Console()

    if not candidates:
        console.print("[bold green]No obvious research gaps found[/bold green] -- nice work.")
        return

    table = Table(title=f"Research priorities in {gedcom_file}")
    table.add_column("Rank", justify="right")
    table.add_column("Name")
    table.add_column("ID")
    table.add_column("Descendants", justify="right")
    table.add_column("Gaps")
    table.add_column("Score", justify="right")

    for rank, candidate in enumerate(candidates[:limit], start=1):
        table.add_row(
            str(rank),
            candidate.individual.full_name,
            candidate.individual.xref_id,
            str(candidate.descendant_count),
            ", ".join(candidate.gaps),
            str(candidate.score),
        )

    console.print(table)

    if len(candidates) > limit:
        console.print(f"\n...and {len(candidates) - limit} more. Use --limit to see more.")
