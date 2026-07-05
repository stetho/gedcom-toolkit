from __future__ import annotations

import click
import networkx as nx
from rich.console import Console
from rich.table import Table

from gedcomtoolkit.graph import build_graph
from gedcomtoolkit.parser import parse_gedcom


@click.command()
@click.argument("gedcom_file", type=click.Path(exists=True))
def command(gedcom_file: str):
    """Print summary statistics for a GEDCOM file."""
    tree = parse_gedcom(gedcom_file)
    g = build_graph(tree)

    console = Console()

    n_individuals = len(tree.individuals)
    n_families = len(tree.families)
    n_living = sum(1 for i in tree.individuals.values() if i.is_living)
    n_with_no_birth_date = sum(1 for i in tree.individuals.values() if not i.birth_date)

    weakly_connected = list(nx.weakly_connected_components(g))
    n_components = len(weakly_connected)
    largest_component = max((len(c) for c in weakly_connected), default=0)

    table = Table(title=f"Stats for {gedcom_file}")
    table.add_column("Metric")
    table.add_column("Value", justify="right")

    table.add_row("Individuals", str(n_individuals))
    table.add_row("Families", str(n_families))
    table.add_row("Presumed living (no death recorded)", str(n_living))
    table.add_row("Missing birth date", str(n_with_no_birth_date))
    table.add_row("Disconnected components", str(n_components))
    table.add_row("Largest component size", str(largest_component))

    console.print(table)
