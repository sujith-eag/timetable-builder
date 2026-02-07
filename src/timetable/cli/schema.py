"""
Schema command group for timetable CLI.

JSON Schema validation commands.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.table import Table

from timetable.core.schema import SchemaValidator
from timetable.core.exceptions import TimetableError, DataLoadError
from .utils import (
    console,
    get_data_dir,
    print_success,
    print_error,
)


@click.group()
@click.pass_context
def schema(ctx: click.Context) -> None:
    """
    JSON Schema validation commands.

    Validate data files against JSON Schema definitions.

    \b
    Examples:
        timetable schema list
        timetable schema validate faculty --data-dir ./data
    """
    pass


@schema.command(name="list")
@click.pass_context
def schema_list(ctx: click.Context) -> None:
    """List available JSON schemas."""
    validator = SchemaValidator()

    table = Table(title="Available JSON Schemas", show_header=True)
    table.add_column("Schema Name", style="cyan")
    table.add_column("File", style="green")

    for name in sorted(validator.list_schemas()):
        file_path = validator.SCHEMA_MAP.get(name, "unknown")
        table.add_row(name, file_path)

    console.print(table)


@schema.command(name="validate")
@click.argument("schema_name")
@click.option(
    "-f", "--file",
    type=click.Path(exists=True),
    help="File to validate.",
)
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.pass_context
def schema_validate(
    ctx: click.Context,
    schema_name: str,
    file: Optional[str],
    data_dir: Optional[str],
) -> None:
    """
    Validate a file against a JSON schema.

    SCHEMA_NAME is the name of the schema (e.g., config, faculty, subjects_full).

    \b
    Examples:
        timetable schema validate faculty -f stage_1/facultyBasic.json
        timetable schema validate subjects_full --data-dir ./data
    """
    try:
        data_path = get_data_dir(data_dir) if data_dir else Path.cwd()
        validator = SchemaValidator(data_path / "schemas" if (data_path / "schemas").exists() else None)

        # Determine file to validate
        if file:
            file_path = Path(file)
        else:
            # Try to infer file from schema name
            file_map = {
                "config": "stage_1/config.json",
                "faculty": "stage_1/facultyBasic.json",
                "subjects_full": "stage_2/subjects2Full.json",
                "faculty_full": "stage_2/faculty2Full.json",
                "teaching_assignments": "stage_3/teachingAssignments_sem1.json",
                "overlap_constraints": "stage_3/studentGroupOverlapConstraints.json",
                "statistics": "stage_3/statistics.json",
                "scheduling_input": "stage_4/schedulingInput.json",
                "ai_schedule": "stage_5/ai_solved_schedule.json",
                "enriched_timetable": "stage_6/timetable_enriched.json",
            }
            if schema_name in file_map:
                file_path = data_path / file_map[schema_name]
            else:
                raise click.ClickException(
                    f"Cannot infer file for schema '{schema_name}'. Use --file to specify."
                )

        if not file_path.exists():
            raise click.ClickException(f"File not found: {file_path}")

        console.print(f"Validating [cyan]{file_path}[/cyan] against schema [green]{schema_name}[/green]...")

        errors = validator.validate_file(file_path, schema_name)

        if errors:
            print_error(f"Validation failed with {len(errors)} error(s):")
            for error in errors[:10]:  # Show first 10 errors
                console.print(f"  [red]•[/red] {error}")
            if len(errors) > 10:
                console.print(f"  ... and {len(errors) - 10} more errors")
            sys.exit(1)
        else:
            print_success(f"Validation passed! File conforms to {schema_name} schema.")

    except DataLoadError as e:
        print_error(str(e))
        sys.exit(1)
    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)
