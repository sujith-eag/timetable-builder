"""
Timetable CLI package.

Modular command-line interface for timetable data management.
"""

import click

from .utils import console
from .status import status
from .validate import validate
from .info import info
from .load import load
from .schema import schema
from .export import export
from .build import build


@click.group()
@click.version_option(version="0.1.0", prog_name="timetable")
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Enable verbose output.",
)
@click.option(
    "-q", "--quiet",
    is_flag=True,
    help="Suppress non-essential output.",
)
@click.pass_context
def cli(ctx: click.Context, verbose: bool, quiet: bool) -> None:
    """
    Timetable Data Management CLI.

    A command-line tool for managing timetable data across all stages.
    Use --help on any command for more details.

    \b
    Quick Start:
        timetable status           Show data pipeline status
        timetable validate --all   Validate all stages
        timetable info all         View complete data summary
        timetable build all        Build all stages
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet


# Register all command groups
cli.add_command(status)
cli.add_command(validate)
cli.add_command(info)
cli.add_command(load)
cli.add_command(schema)
cli.add_command(export)
cli.add_command(build)


def main() -> None:
    """Entry point for the CLI."""
    cli(obj={})


# Alias main to cli for Click's CliRunner compatibility
main.name = cli.name  # type: ignore


if __name__ == "__main__":
    main()
