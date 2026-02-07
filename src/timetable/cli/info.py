"""
Info command group for timetable CLI.

Displays information about timetable data.
"""

import sys
from typing import Optional

import click
from rich.table import Table
from rich.panel import Panel

from timetable.core.loader import DataLoader
from timetable.core.exceptions import TimetableError
from .utils import (
    console,
    get_data_dir,
    print_success,
    print_error,
    print_warning,
)


@click.group()
@click.pass_context
def info(ctx: click.Context) -> None:
    """
    Display information about timetable data.

    Shows summaries and statistics for various data types.

    \b
    Examples:
        timetable info config --data-dir ./data
        timetable info faculty --data-dir ./data
        timetable info all --data-dir ./data
    """
    pass


@info.command(name="config")
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.pass_context
def info_config(ctx: click.Context, data_dir: Optional[str]) -> None:
    """Display configuration information."""
    try:
        data_path = get_data_dir(data_dir)
        loader = DataLoader(data_path)
        config = loader.load_config()

        # Create config table
        table = Table(title="Configuration Summary", show_header=True)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Day Start", config.day_start)
        table.add_row("Day End", config.day_end)
        table.add_row("Working Days", ", ".join(config.weekdays))
        table.add_row("Time Slots", str(len(config.time_slots)))
        table.add_row("Rooms", str(len(config.resources.rooms)))

        if config.break_windows:
            table.add_row("Breaks", str(len(config.break_windows)))

        console.print(table)

        # Show rooms breakdown
        room_types = {}
        for room in config.resources.rooms:
            room_type = room.type
            room_types[room_type] = room_types.get(room_type, 0) + 1

        console.print("\n[bold]Rooms by Type:[/bold]")
        for rt, count in sorted(room_types.items()):
            console.print(f"  • {rt}: {count}")

    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)


@info.command(name="faculty")
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.option(
    "-s", "--stage",
    type=int,
    default=1,
    help="Stage to load faculty from (1 or 2).",
)
@click.pass_context
def info_faculty(ctx: click.Context, data_dir: Optional[str], stage: int) -> None:
    """Display faculty information."""
    try:
        data_path = get_data_dir(data_dir)
        loader = DataLoader(data_path)

        if stage == 1:
            faculty = loader.load_faculty()
            title = "Faculty Summary (Stage 1)"
        elif stage == 2:
            faculty = loader.load_faculty_full()
            title = "Faculty Summary (Stage 2)"
        else:
            raise click.ClickException("Stage must be 1 or 2")

        table = Table(title=title, show_header=True)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Faculty", str(len(faculty)))

        if stage == 1:
            # Count subjects assigned (assigned + supporting)
            total_subjects = sum(len(f.assigned_subjects) + len(f.supporting_subjects) for f in faculty)
            table.add_row("Total Subject Assignments", str(total_subjects))
        else:
            # Stage 2 - count primary assignments
            total_primary = sum(len(f.primary_assignments) for f in faculty)
            total_supporting = sum(len(f.supporting_assignments) for f in faculty)
            table.add_row("Primary Assignments", str(total_primary))
            table.add_row("Supporting Assignments", str(total_supporting))

        console.print(table)

        # Show first few faculty
        console.print("\n[bold]Faculty Members:[/bold]")
        for i, f in enumerate(faculty[:10]):
            if stage == 1:
                console.print(f"  {i+1}. {f.name} ({f.faculty_id})")
            else:
                console.print(f"  {i+1}. {f.name} ({f.faculty_id}) - Workload: {f.workload_stats.total_weekly_hours}h")

        if len(faculty) > 10:
            console.print(f"  ... and {len(faculty) - 10} more")

    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)


@info.command(name="subjects")
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.option(
    "-s", "--stage",
    type=int,
    default=1,
    help="Stage to load subjects from (1 or 2).",
)
@click.option(
    "--semester",
    type=int,
    help="Filter by semester.",
)
@click.pass_context
def info_subjects(
    ctx: click.Context,
    data_dir: Optional[str],
    stage: int,
    semester: Optional[int],
) -> None:
    """Display subjects information."""
    try:
        data_path = get_data_dir(data_dir)
        loader = DataLoader(data_path)

        if stage == 1:
            subjects = loader.load_subjects(semester=semester)
            title = "Subjects Summary (Stage 1)"
        elif stage == 2:
            subjects = loader.load_subjects_full()
            if semester:
                subjects = [s for s in subjects if s.semester == semester]
            title = "Subjects Summary (Stage 2)"
        else:
            raise click.ClickException("Stage must be 1 or 2")

        if semester:
            title += f" - Semester {semester}"

        table = Table(title=title, show_header=True)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Subjects", str(len(subjects)))

        # Group by semester
        by_semester: dict[int, int] = {}
        for s in subjects:
            sem = s.semester
            by_semester[sem] = by_semester.get(sem, 0) + 1

        for sem, count in sorted(by_semester.items()):
            table.add_row(f"Semester {sem}", str(count))

        if stage == 2:
            # Count components
            total_components = sum(len(s.components) for s in subjects)
            table.add_row("Total Components", str(total_components))

        console.print(table)

        # Show subjects list
        console.print("\n[bold]Subjects:[/bold]")
        for i, s in enumerate(subjects[:15]):
            if stage == 1:
                console.print(f"  {i+1}. [{s.subject_code}] {s.title}")
            else:
                comp_count = len(s.components)
                console.print(f"  {i+1}. [{s.subject_code}] {s.title} ({comp_count} components)")

        if len(subjects) > 15:
            console.print(f"  ... and {len(subjects) - 15} more")

    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)


@info.command(name="scheduling")
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.pass_context
def info_scheduling(ctx: click.Context, data_dir: Optional[str]) -> None:
    """Display scheduling input information."""
    try:
        data_path = get_data_dir(data_dir)
        loader = DataLoader(data_path)
        scheduling_input = loader.load_scheduling_input()

        table = Table(title="Scheduling Input Summary", show_header=True)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Assignments", str(len(scheduling_input.assignments)))
        table.add_row("Semester 1 Assignments", str(scheduling_input.metadata.semester1_assignments))
        table.add_row("Semester 3 Assignments", str(scheduling_input.metadata.semester3_assignments))
        table.add_row("Time Slots", str(scheduling_input.metadata.total_time_slots))
        table.add_row("Rooms", str(scheduling_input.metadata.total_rooms))
        table.add_row("Working Days", ", ".join(scheduling_input.configuration.weekdays))

        console.print(table)

        # Show assignment breakdown by component type
        component_types = {}
        for assignment in scheduling_input.assignments:
            comp_type = assignment.component_type
            component_types[comp_type] = component_types.get(comp_type, 0) + 1

        console.print("\n[bold]Assignments by Component Type:[/bold]")
        for comp_type, count in sorted(component_types.items()):
            console.print(f"  • {comp_type}: {count}")

        # Show first few assignments
        console.print("\n[bold]Sample Assignments:[/bold]")
        for i, assignment in enumerate(scheduling_input.assignments[:10]):
            console.print(f"  {i+1}. [{assignment.subject_code}] {assignment.subject_title}")
            console.print(f"      Faculty: {assignment.faculty_name}, Sessions: {assignment.sessions_per_week}")

        if len(scheduling_input.assignments) > 10:
            console.print(f"  ... and {len(scheduling_input.assignments) - 10} more")

    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)


@info.command(name="all")
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.pass_context
def info_all(ctx: click.Context, data_dir: Optional[str]) -> None:
    """Display complete data summary."""
    try:
        data_path = get_data_dir(data_dir)
        loader = DataLoader(data_path)

        console.print(Panel.fit("[bold]Timetable Data Summary[/bold]", border_style="blue"))

        # Stage 1 Summary
        console.print("\n[bold cyan]Stage 1 - Input Data[/bold cyan]")
        try:
            config = loader.load_config()
            print_success(f"Config: {len(config.time_slots)} slots, {len(config.resources.rooms)} rooms")

            faculty = loader.load_faculty()
            print_success(f"Faculty: {len(faculty)} members")

            subjects = loader.load_subjects()
            print_success(f"Subjects: {len(subjects)} total")

            groups = loader.load_student_groups()
            print_success(f"Student Groups: {len(groups.student_groups)} groups")
        except TimetableError as e:
            print_error(f"Stage 1: {e}")

        # Stage 2 Summary
        console.print("\n[bold cyan]Stage 2 - Enriched Data[/bold cyan]")
        try:
            faculty = loader.load_faculty_full()
            print_success(f"Faculty Full: {len(faculty)} with workload data")

            subjects = loader.load_subjects_full()
            print_success(f"Subjects Full: {len(subjects)} with components")
        except TimetableError as e:
            print_warning(f"Stage 2: {e}")

        # Stage 3 Summary
        console.print("\n[bold cyan]Stage 3 - Assignments[/bold cyan]")
        try:
            assignments = loader.load_all_teaching_assignments()
            for sem, data in assignments.items():
                print_success(f"Semester {sem}: {len(data.assignments)} assignments")

            stats = loader.load_statistics()
            print_success(f"Total: {stats.combined.total_assignments} assignments")
        except TimetableError as e:
            print_warning(f"Stage 3: {e}")

        # Stage 4 Summary
        console.print("\n[bold cyan]Stage 4 - AI Input[/bold cyan]")
        try:
            scheduling_input = loader.load_scheduling_input()
            print_success(f"Scheduling Input: {len(scheduling_input.assignments)} assignments for AI")
            print_success(f"Time Slots: {scheduling_input.metadata.total_time_slots}, Rooms: {scheduling_input.metadata.total_rooms}")
        except TimetableError as e:
            print_warning(f"Stage 4: {e}")

        # Stage 5 Summary
        console.print("\n[bold cyan]Stage 5 - AI Output[/bold cyan]")
        try:
            ai_schedule = loader.load_ai_schedule()
            print_success(f"AI Schedule: {len(ai_schedule.schedule)} scheduled sessions")
        except TimetableError as e:
            print_warning(f"Stage 5: {e}")

        # Stage 6 Summary
        console.print("\n[bold cyan]Stage 6 - Enriched Output[/bold cyan]")
        try:
            enriched_timetable = loader.load_enriched_timetable()
            print_success(f"Enriched Timetable: {enriched_timetable.metadata.total_sessions} complete sessions")
        except TimetableError as e:
            print_warning(f"Stage 6: {e}")

    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)
