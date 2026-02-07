"""
Validate command for timetable CLI.

Validates data files across all stages.
"""

import sys
from typing import Optional

import click
from pydantic import ValidationError
from rich.panel import Panel

from timetable.core.loader import DataLoader
from timetable.core.exceptions import TimetableError, DataLoadError
from .utils import (
    console,
    get_data_dir,
    print_header,
    print_success,
    print_error,
    print_warning,
    create_progress,
)


@click.command()
@click.option(
    "-s", "--stage",
    type=int,
    help="Stage number to validate (1, 2, or 3).",
)
@click.option(
    "-a", "--all",
    "validate_all",
    is_flag=True,
    help="Validate all stages.",
)
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.option(
    "--strict",
    is_flag=True,
    help="Treat warnings as errors.",
)
@click.pass_context
def validate(
    ctx: click.Context,
    stage: Optional[int],
    validate_all: bool,
    data_dir: Optional[str],
    strict: bool,
) -> None:
    """
    Validate timetable data files.

    Checks data files against Pydantic models to ensure they are
    correctly structured and contain valid data.

    \b
    Examples:
        timetable validate --stage 1
        timetable validate --all --data-dir ./data
        timetable validate --stage 2 --strict
    """
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    try:
        data_path = get_data_dir(data_dir)
        loader = DataLoader(data_path, strict=strict)

        stages_to_validate = []
        if validate_all:
            stages_to_validate = [1, 2, 3]
        elif stage:
            if stage not in [1, 2, 3]:
                raise click.ClickException(
                    f"Invalid stage: {stage}. Must be 1, 2, or 3."
                )
            stages_to_validate = [stage]
        else:
            raise click.ClickException(
                "Specify --stage NUMBER or --all to validate."
            )

        errors = []
        warnings = []
        results = []

        if not quiet:
            print_header(
                "Data Validation",
                f"Validating Stage(s): {', '.join(map(str, stages_to_validate))}"
            )
            console.print()

        with create_progress() as progress:
            task = progress.add_task(
                "Validating...",
                total=len(stages_to_validate),
                status="Starting"
            )

            for s in stages_to_validate:
                progress.update(task, status=f"Stage {s}")

                try:
                    if s == 1:
                        result = _validate_stage1(loader, verbose)
                    elif s == 2:
                        result = _validate_stage2(loader, verbose)
                    elif s == 3:
                        result = _validate_stage3(loader, verbose)
                    else:
                        continue

                    results.append((s, result))

                    if not result["success"]:
                        errors.extend(result.get("errors", []))
                    
                    warnings.extend(result.get("warnings", []))

                except DataLoadError as e:
                    errors.append(f"Stage {s}: {e}")
                    results.append((s, {"success": False, "errors": [str(e)]}))
                except ValidationError as e:
                    errors.append(f"Stage {s}: {e}")
                    results.append((s, {"success": False, "errors": [str(e)]}))

                progress.update(task, advance=1)

            progress.update(task, status="Complete")

        # Print results summary
        if not quiet:
            console.print()
            for s, result in results:
                if result["success"]:
                    print_success(f"Stage {s} validation passed")
                    if verbose:
                        for item in result.get("items", []):
                            console.print(f"    [dim]• {item}[/dim]")
                else:
                    print_error(f"Stage {s} validation failed")

            console.print()

        if warnings:
            console.print("[yellow]Warnings:[/yellow]")
            for w in warnings:
                print_warning(w)
            console.print()

        if errors:
            console.print("[red]Errors:[/red]")
            for e in errors:
                print_error(e)
            sys.exit(1)
        else:
            if not quiet:
                console.print(
                    Panel.fit(
                        "[bold green]✓ All validations passed![/bold green]",
                        border_style="green"
                    )
                )
            sys.exit(0)

    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)


def _validate_stage1(loader: DataLoader, verbose: bool) -> dict:
    """Validate Stage 1 data."""
    items = []
    warnings = []

    try:
        config = loader.load_config()
        items.append(f"Config: {len(config.time_slots)} time slots, {len(config.resources.rooms)} rooms")

        faculty = loader.load_faculty()
        items.append(f"Faculty: {len(faculty)} members")

        subjects = loader.load_subjects()
        items.append(f"Subjects: {len(subjects)} total")

        groups = loader.load_student_groups()
        items.append(
            f"Student Groups: {len(groups.student_groups)} groups, "
            f"{len(groups.elective_student_groups)} elective groups"
        )

        # Get cross-validation warnings
        warnings = loader.validate_stage1()

        return {"success": True, "items": items, "warnings": warnings}

    except (DataLoadError, ValidationError) as e:
        return {"success": False, "errors": [str(e)], "warnings": []}


def _validate_stage2(loader: DataLoader, verbose: bool) -> dict:
    """Validate Stage 2 data."""
    items = []

    try:
        faculty = loader.load_faculty_full()
        items.append(f"Faculty Full: {len(faculty)} members with assignments")

        subjects = loader.load_subjects_full()
        items.append(f"Subjects Full: {len(subjects)} subjects with components")

        return {"success": True, "items": items, "warnings": []}

    except (DataLoadError, ValidationError) as e:
        return {"success": False, "errors": [str(e)], "warnings": []}


def _validate_stage3(loader: DataLoader, verbose: bool) -> dict:
    """Validate Stage 3 data."""
    items = []

    try:
        # Load assignments for available semesters
        assignments = loader.load_all_teaching_assignments()
        for sem, data in assignments.items():
            items.append(f"Semester {sem}: {len(data.assignments)} assignments")

        overlaps = loader.load_overlap_constraints()
        items.append(f"Overlap constraints: {len(overlaps.cannot_overlap_with)} groups")

        stats = loader.load_statistics()
        items.append(f"Statistics: {stats.combined.total_assignments} total assignments")

        return {"success": True, "items": items, "warnings": []}

    except (DataLoadError, ValidationError) as e:
        return {"success": False, "errors": [str(e)], "warnings": []}
