"""
CLI entry point.

To add a new subcommand later:
  1. Create gedcomtoolkit/commands/yourcommand.py
  2. Define a Click command called `command` (any name works, but be consistent)
  3. Import and register it below with cli.add_command(...)

That's the whole extension point -- no other file needs to change.
"""

from __future__ import annotations

import click

from gedcomtoolkit.commands import (
    completeness,
    duplicates,
    findid,
    findrelationship,
    places,
    rn,
    sources,
    stats,
    validate,
)


@click.group()
@click.version_option()
def cli():
    """gedcom: explore, validate, and query GEDCOM family tree files."""
    pass


cli.add_command(stats.command, name="stats")
cli.add_command(validate.command, name="validate")
cli.add_command(findid.command, name="findid")
cli.add_command(findrelationship.command, name="findrelationship")
cli.add_command(rn.command, name="rn")
cli.add_command(sources.command, name="sources")
cli.add_command(places.command, name="places")
cli.add_command(duplicates.command, name="duplicates")
cli.add_command(completeness.command, name="completeness")


if __name__ == "__main__":
    cli()
