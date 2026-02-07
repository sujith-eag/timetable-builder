"""
Load command group for timetable CLI.

Loads and displays timetable data with optional JSON output.
"""

import sys
import json
from typing import Optional

import click
from rich.table import Table
from rich.panel import Panel

from timetable.core.loader import DataLoader
from timetable.core.exceptions import TimetableError
from .utils import (
    console,
    get_data_dir,
    print_error,
)


@click.group()
@click.pass_context
def load(ctx: click.Context) -> None:
    """
    Load and display timetable data.

    Shows detailed data from JSON files with optional JSON output.

    \b
    Examples:
        timetable load config --data-dir ./data
        timetable load faculty --stage 2 --data-dir ./data
        timetable load subjects --semester 1 --json
    """
    pass


@load.command(name="config")
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.option(
    "--json", "output_json",
    is_flag=True,
    help="Output as JSON.",
)
@click.pass_context
def load_config(ctx: click.Context, data_dir: Optional[str], output_json: bool) -> None:
    """Load and display configuration."""
    try:
        data_path = get_data_dir(data_dir)
        loader = DataLoader(data_path)
        config = loader.load_config()

        if output_json:
            console.print_json(config.model_dump_json(indent=2))
        else:
            # Display as table
            table = Table(title="Configuration", show_header=True)
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("Day Start", config.day_start)
            table.add_row("Day End", config.day_end)
            table.add_row("Working Days", ", ".join(config.weekdays))
            table.add_row("Time Slots", str(len(config.time_slots)))
            table.add_row("Rooms", str(len(config.resources.rooms)))
            table.add_row("Breaks", str(len(config.break_windows) if config.break_windows else 0))

            console.print(table)

            # Show time slots
            console.print("\n[bold]Time Slots:[/bold]")
            for slot in config.time_slots[:5]:
                console.print(f"  Slot {slot.slot_id}: {slot.start} - {slot.end} ({slot.length_minutes} min)")
            if len(config.time_slots) > 5:
                console.print(f"  ... and {len(config.time_slots) - 5} more")

    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)


@load.command(name="faculty")
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.option(
    "-s", "--stage",
    type=int,
    default=1,
    help="Stage to load from (1 or 2).",
)
@click.option(
    "--json", "output_json",
    is_flag=True,
    help="Output as JSON.",
)
@click.pass_context
def load_faculty(
    ctx: click.Context,
    data_dir: Optional[str],
    stage: int,
    output_json: bool,
) -> None:
    """Load and display faculty data."""
    try:
        data_path = get_data_dir(data_dir)
        loader = DataLoader(data_path)

        if stage == 1:
            faculty = loader.load_faculty()
        elif stage == 2:
            faculty = loader.load_faculty_full()
        else:
            raise click.ClickException("Stage must be 1 or 2")

        if output_json:
            data = [f.model_dump() for f in faculty]
            console.print_json(json.dumps(data, indent=2))
        else:
            table = Table(title=f"Faculty (Stage {stage})", show_header=True)
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="white")

            if stage == 1:
                table.add_column("Subjects", style="green")
                for f in faculty:
                    # Combine assigned and supporting subjects for display
                    all_subjects = [str(s) for s in f.assigned_subjects[:2]] + f.supporting_subjects[:1]
                    display = ", ".join(all_subjects[:3]) + ("..." if len(f.assigned_subjects) + len(f.supporting_subjects) > 3 else "")
                    table.add_row(
                        f.faculty_id,
                        f.name,
                        display
                    )
            else:
                table.add_column("Workload", style="green")
                table.add_column("Primary", style="yellow")
                for f in faculty:
                    table.add_row(
                        f.faculty_id,
                        f.name,
                        f"{f.workload_stats.total_weekly_hours}h",
                        str(len(f.primary_assignments))
                    )

            console.print(table)

    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)


@load.command(name="subjects")
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.option(
    "-s", "--stage",
    type=int,
    default=1,
    help="Stage to load from (1 or 2).",
)
@click.option(
    "--semester",
    type=int,
    help="Filter by semester.",
)
@click.option(
    "--json", "output_json",
    is_flag=True,
    help="Output as JSON.",
)
@click.pass_context
def load_subjects(
    ctx: click.Context,
    data_dir: Optional[str],
    stage: int,
    semester: Optional[int],
    output_json: bool,
) -> None:
    """Load and display subjects data."""
    try:
        data_path = get_data_dir(data_dir)
        loader = DataLoader(data_path)

        if stage == 1:
            subjects = loader.load_subjects(semester=semester)
        elif stage == 2:
            subjects = loader.load_subjects_full()
            if semester:
                subjects = [s for s in subjects if s.semester == semester]
        else:
            raise click.ClickException("Stage must be 1 or 2")

        if output_json:
            data = [s.model_dump() for s in subjects]
            console.print_json(json.dumps(data, indent=2))
        else:
            title = f"Subjects (Stage {stage})"
            if semester:
                title += f" - Semester {semester}"

            table = Table(title=title, show_header=True)
            table.add_column("Code", style="cyan")
            table.add_column("Name", style="white")
            table.add_column("Sem", style="yellow")

            if stage == 2:
                table.add_column("Components", style="green")

            for s in subjects:
                if stage == 1:
                    table.add_row(s.subject_code, s.title, str(s.semester))
                else:
                    comp_str = ", ".join([c.component_type for c in s.components[:2]])
                    if len(s.components) > 2:
                        comp_str += f" (+{len(s.components) - 2})"
                    table.add_row(s.subject_code, s.title, str(s.semester), comp_str)

            console.print(table)

    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)


@load.command(name="assignments")
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.option(
    "--semester",
    type=int,
    required=True,
    help="Semester number (1 or 3).",
)
@click.option(
    "--json", "output_json",
    is_flag=True,
    help="Output as JSON.",
)
@click.pass_context
def load_assignments(
    ctx: click.Context,
    data_dir: Optional[str],
    semester: int,
    output_json: bool,
) -> None:
    """Load and display teaching assignments."""
    try:
        data_path = get_data_dir(data_dir)
        loader = DataLoader(data_path)

        assignments_file = loader.load_teaching_assignments(semester)

        if output_json:
            console.print_json(assignments_file.model_dump_json(indent=2))
        else:
            console.print(Panel.fit(
                f"[bold]Teaching Assignments - Semester {semester}[/bold]",
                border_style="blue"
            ))

            # Show metadata
            meta = assignments_file.metadata
            console.print(f"\n[bold]Generated:[/bold] {meta.generated_at}")
            console.print(f"[bold]Generator:[/bold] {meta.generator}")

            # Show statistics
            stats = assignments_file.statistics
            console.print("\n[bold]Statistics:[/bold]")
            console.print(f"  • Total Assignments: {stats.total_assignments}")
            console.print(f"  • Total Sessions: {stats.total_sessions}")
            console.print(f"  • Total Weekly Hours: {stats.total_weekly_hours}")

            # Show assignments table
            table = Table(title=f"Assignments ({len(assignments_file.assignments)} total)", show_header=True)
            table.add_column("ID", style="cyan")
            table.add_column("Subject", style="white")
            table.add_column("Faculty", style="green")
            table.add_column("Component", style="yellow")

            for a in assignments_file.assignments[:20]:
                table.add_row(
                    a.assignment_id,
                    a.subject_code,
                    a.faculty_id,
                    a.component_type
                )

            if len(assignments_file.assignments) > 20:
                table.add_row("...", f"({len(assignments_file.assignments) - 20} more)", "", "")

            console.print(table)

    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)


@load.command(name="statistics")
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.option(
    "--json", "output_json",
    is_flag=True,
    help="Output as JSON.",
)
@click.pass_context
def load_statistics(ctx: click.Context, data_dir: Optional[str], output_json: bool) -> None:
    """Load and display Stage 3 statistics."""
    try:
        data_path = get_data_dir(data_dir)
        loader = DataLoader(data_path)

        stats = loader.load_statistics()

        if output_json:
            console.print_json(stats.model_dump_json(indent=2))
        else:
            console.print(Panel.fit("[bold]Stage 3 Statistics[/bold]", border_style="blue"))

            # Combined stats
            combined = stats.combined
            console.print("\n[bold cyan]Combined Statistics:[/bold cyan]")

            table = Table(show_header=True)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Total Assignments", str(combined.total_assignments))
            table.add_row("Total Sessions", str(combined.total_sessions))
            table.add_row("Total Hours", f"{combined.total_hours:.1f}")

            console.print(table)

            # Resource analysis
            ra = combined.resource_analysis
            console.print("\n[bold cyan]Resource Analysis:[/bold cyan]")
            console.print(f"  • Lecture Room Sessions: {ra.lecture_room_sessions}")
            console.print(f"  • Lab Sessions: {ra.lab_sessions}")
            console.print(f"  • Theory Sessions: {ra.theory_sessions}")
            console.print(f"  • Practical Sessions: {ra.practical_sessions}")
            console.print(f"  • Tutorial Sessions: {ra.tutorial_sessions}")

            # Semester breakdown
            for sem_key, sem_stats in [("semester1", stats.semester1), ("semester3", stats.semester3)]:
                if sem_stats:
                    console.print(f"\n[bold cyan]Semester {sem_stats.semester}:[/bold cyan]")
                    console.print(f"  • Assignments: {sem_stats.total_assignments}")
                    console.print(f"  • Sessions: {sem_stats.total_sessions}")
                    console.print(f"  • Hours: {sem_stats.total_hours:.1f}")

    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)
