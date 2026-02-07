"""
Export command group for timetable CLI.

Exports data to JSON, CSV, and Markdown formats.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.table import Table

from timetable.core.loader import DataLoader
from timetable.core.exceptions import TimetableError
from .utils import (
    console,
    get_data_dir,
    print_success,
    print_error,
    print_warning,
    create_progress,
    export_to_json,
    export_to_csv,
    export_to_markdown,
)


@click.group()
@click.pass_context
def export(ctx: click.Context) -> None:
    """
    Export data to various formats.

    Supports JSON, CSV, and Markdown exports.

    \b
    Examples:
        timetable export faculty --format csv --output ./exports
        timetable export assignments --format md --semester 1
        timetable export all --format json --output ./backup
    """
    pass


@export.command(name="faculty")
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.option(
    "-s", "--stage",
    type=int,
    default=2,
    help="Stage to export from (1 or 2).",
)
@click.option(
    "-f", "--format",
    "output_format",
    type=click.Choice(["json", "csv", "md"]),
    default="json",
    help="Output format.",
)
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output directory.",
)
@click.pass_context
def export_faculty(
    ctx: click.Context,
    data_dir: Optional[str],
    stage: int,
    output_format: str,
    output: Optional[str],
) -> None:
    """Export faculty data to file."""
    try:
        data_path = get_data_dir(data_dir)
        loader = DataLoader(data_path)
        
        output_dir = Path(output) if output else data_path / "exports"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with create_progress() as progress:
            task = progress.add_task("Exporting faculty...", total=3, status="Loading")
            
            # Use appropriate method based on stage
            if stage == 1:
                faculty = loader.load_faculty()
            else:
                faculty = loader.load_faculty_full()
            progress.update(task, advance=1, status="Processing")
            
            # Convert to dict
            faculty_data = [f.model_dump(mode="json") for f in faculty]
            progress.update(task, advance=1, status="Writing")
            
            # Export based on format
            filename = f"faculty_stage{stage}_{timestamp}"
            if output_format == "json":
                filepath = output_dir / f"{filename}.json"
                export_to_json({"faculty": faculty_data, "count": len(faculty_data)}, filepath)
            elif output_format == "csv":
                filepath = output_dir / f"{filename}.csv"
                export_to_csv(faculty_data, filepath)
            elif output_format == "md":
                filepath = output_dir / f"{filename}.md"
                export_to_markdown(faculty_data, filepath, f"Faculty Data (Stage {stage})")
            
            progress.update(task, advance=1, status="Complete")
        
        print_success(f"Exported {len(faculty_data)} faculty members to {filepath}")
        
    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)


@export.command(name="subjects")
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.option(
    "-s", "--stage",
    type=int,
    default=2,
    help="Stage to export from (1 or 2).",
)
@click.option(
    "--semester",
    type=int,
    help="Filter by semester.",
)
@click.option(
    "-f", "--format",
    "output_format",
    type=click.Choice(["json", "csv", "md"]),
    default="json",
    help="Output format.",
)
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output directory.",
)
@click.pass_context
def export_subjects(
    ctx: click.Context,
    data_dir: Optional[str],
    stage: int,
    semester: Optional[int],
    output_format: str,
    output: Optional[str],
) -> None:
    """Export subjects data to file."""
    try:
        data_path = get_data_dir(data_dir)
        loader = DataLoader(data_path)
        
        output_dir = Path(output) if output else data_path / "exports"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with create_progress() as progress:
            task = progress.add_task("Exporting subjects...", total=3, status="Loading")
            
            # Use appropriate method based on stage
            if stage == 1:
                subjects = loader.load_subjects(semester=semester)
            else:
                all_subjects = loader.load_subjects_full()
                if semester:
                    subjects = [s for s in all_subjects if s.semester == semester]
                else:
                    subjects = all_subjects
            progress.update(task, advance=1, status="Processing")
            
            subjects_data = [s.model_dump(mode="json") for s in subjects]
            progress.update(task, advance=1, status="Writing")
            
            sem_suffix = f"_sem{semester}" if semester else ""
            filename = f"subjects_stage{stage}{sem_suffix}_{timestamp}"
            
            if output_format == "json":
                filepath = output_dir / f"{filename}.json"
                export_to_json({"subjects": subjects_data, "count": len(subjects_data)}, filepath)
            elif output_format == "csv":
                filepath = output_dir / f"{filename}.csv"
                export_to_csv(subjects_data, filepath)
            elif output_format == "md":
                filepath = output_dir / f"{filename}.md"
                title = f"Subjects (Stage {stage})"
                if semester:
                    title += f" - Semester {semester}"
                export_to_markdown(subjects_data, filepath, title)
            
            progress.update(task, advance=1, status="Complete")
        
        print_success(f"Exported {len(subjects_data)} subjects to {filepath}")
        
    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)


@export.command(name="assignments")
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.option(
    "--semester",
    type=int,
    default=1,
    help="Semester to export (1 or 3).",
)
@click.option(
    "-f", "--format",
    "output_format",
    type=click.Choice(["json", "csv", "md"]),
    default="json",
    help="Output format.",
)
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output directory.",
)
@click.pass_context
def export_assignments(
    ctx: click.Context,
    data_dir: Optional[str],
    semester: int,
    output_format: str,
    output: Optional[str],
) -> None:
    """Export teaching assignments to file."""
    try:
        data_path = get_data_dir(data_dir)
        loader = DataLoader(data_path)
        
        output_dir = Path(output) if output else data_path / "exports"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with create_progress() as progress:
            task = progress.add_task("Exporting assignments...", total=3, status="Loading")
            
            assignments_file = loader.load_teaching_assignments(semester=semester)
            progress.update(task, advance=1, status="Processing")
            
            assignments_data = [a.model_dump(mode="json") for a in assignments_file.assignments]
            progress.update(task, advance=1, status="Writing")
            
            filename = f"assignments_sem{semester}_{timestamp}"
            
            if output_format == "json":
                filepath = output_dir / f"{filename}.json"
                export_to_json({
                    "assignments": assignments_data,
                    "count": len(assignments_data),
                    "semester": semester,
                    "metadata": assignments_file.metadata.model_dump(mode="json") if assignments_file.metadata else None
                }, filepath)
            elif output_format == "csv":
                filepath = output_dir / f"{filename}.csv"
                export_to_csv(assignments_data, filepath)
            elif output_format == "md":
                filepath = output_dir / f"{filename}.md"
                export_to_markdown(assignments_data, filepath, f"Teaching Assignments - Semester {semester}")
            
            progress.update(task, advance=1, status="Complete")
        
        print_success(f"Exported {len(assignments_data)} assignments to {filepath}")
        
    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)


@export.command(name="statistics")
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.option(
    "-f", "--format",
    "output_format",
    type=click.Choice(["json", "csv", "md"]),
    default="json",
    help="Output format.",
)
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output directory.",
)
@click.pass_context
def export_statistics(
    ctx: click.Context,
    data_dir: Optional[str],
    output_format: str,
    output: Optional[str],
) -> None:
    """Export Stage 3 statistics to file."""
    try:
        data_path = get_data_dir(data_dir)
        loader = DataLoader(data_path)
        
        output_dir = Path(output) if output else data_path / "exports"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with create_progress() as progress:
            task = progress.add_task("Exporting statistics...", total=3, status="Loading")
            
            stats = loader.load_statistics()
            progress.update(task, advance=1, status="Processing")
            
            stats_data = stats.model_dump(mode="json")
            progress.update(task, advance=1, status="Writing")
            
            filename = f"statistics_{timestamp}"
            
            if output_format == "json":
                filepath = output_dir / f"{filename}.json"
                export_to_json(stats_data, filepath)
            elif output_format == "csv":
                # Flatten for CSV
                filepath = output_dir / f"{filename}.csv"
                flat_data = [
                    {"type": "semester1", **stats.semester1.model_dump(mode="json")},
                    {"type": "semester3", **stats.semester3.model_dump(mode="json")},
                    {"type": "combined", **stats.combined.model_dump(mode="json")},
                ]
                export_to_csv(flat_data, filepath)
            elif output_format == "md":
                filepath = output_dir / f"{filename}.md"
                # Create summary for markdown
                summary = [
                    {"Metric": "Semester 1 Assignments", "Value": stats.semester1.total_assignments},
                    {"Metric": "Semester 1 Sessions/Week", "Value": stats.semester1.total_sessions_per_week},
                    {"Metric": "Semester 3 Assignments", "Value": stats.semester3.total_assignments},
                    {"Metric": "Semester 3 Sessions/Week", "Value": stats.semester3.total_sessions_per_week},
                    {"Metric": "Total Assignments", "Value": stats.combined.total_assignments},
                    {"Metric": "Total Sessions/Week", "Value": stats.combined.total_sessions_per_week},
                ]
                export_to_markdown(summary, filepath, "Stage 3 Statistics")
            
            progress.update(task, advance=1, status="Complete")
        
        print_success(f"Exported statistics to {filepath}")
        
    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)


@export.command(name="all")
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.option(
    "-f", "--format",
    "output_format",
    type=click.Choice(["json", "csv", "md"]),
    default="json",
    help="Output format.",
)
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output directory.",
)
@click.pass_context
def export_all(
    ctx: click.Context,
    data_dir: Optional[str],
    output_format: str,
    output: Optional[str],
) -> None:
    """Export all data to files."""
    try:
        data_path = get_data_dir(data_dir)
        loader = DataLoader(data_path)
        
        output_dir = Path(output) if output else data_path / "exports"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = output_dir / f"export_{timestamp}"
        export_dir.mkdir(parents=True, exist_ok=True)
        
        exported_files = []
        
        with create_progress() as progress:
            task = progress.add_task("Exporting all data...", total=6, status="Starting")
            
            # Faculty Stage 2
            try:
                faculty = loader.load_faculty_full()
                faculty_data = [f.model_dump(mode="json") for f in faculty]
                if output_format == "json":
                    fp = export_dir / "faculty.json"
                    export_to_json({"faculty": faculty_data}, fp)
                elif output_format == "csv":
                    fp = export_dir / "faculty.csv"
                    export_to_csv(faculty_data, fp)
                else:
                    fp = export_dir / "faculty.md"
                    export_to_markdown(faculty_data, fp, "Faculty")
                exported_files.append(("Faculty", len(faculty_data)))
            except Exception as e:
                print_warning(f"Could not export faculty: {e}")
            progress.update(task, advance=1, status="Faculty done")
            
            # Subjects Stage 2
            try:
                subjects = loader.load_subjects_full()
                subjects_data = [s.model_dump(mode="json") for s in subjects]
                if output_format == "json":
                    fp = export_dir / "subjects.json"
                    export_to_json({"subjects": subjects_data}, fp)
                elif output_format == "csv":
                    fp = export_dir / "subjects.csv"
                    export_to_csv(subjects_data, fp)
                else:
                    fp = export_dir / "subjects.md"
                    export_to_markdown(subjects_data, fp, "Subjects")
                exported_files.append(("Subjects", len(subjects_data)))
            except Exception as e:
                print_warning(f"Could not export subjects: {e}")
            progress.update(task, advance=1, status="Subjects done")
            
            # Assignments Sem 1
            try:
                assignments1 = loader.load_teaching_assignments(semester=1)
                assign_data = [a.model_dump(mode="json") for a in assignments1.assignments]
                if output_format == "json":
                    fp = export_dir / "assignments_sem1.json"
                    export_to_json({"assignments": assign_data}, fp)
                elif output_format == "csv":
                    fp = export_dir / "assignments_sem1.csv"
                    export_to_csv(assign_data, fp)
                else:
                    fp = export_dir / "assignments_sem1.md"
                    export_to_markdown(assign_data, fp, "Assignments Semester 1")
                exported_files.append(("Assignments Sem 1", len(assign_data)))
            except Exception as e:
                print_warning(f"Could not export semester 1 assignments: {e}")
            progress.update(task, advance=1, status="Sem 1 done")
            
            # Assignments Sem 3
            try:
                assignments3 = loader.load_teaching_assignments(semester=3)
                assign_data = [a.model_dump(mode="json") for a in assignments3.assignments]
                if output_format == "json":
                    fp = export_dir / "assignments_sem3.json"
                    export_to_json({"assignments": assign_data}, fp)
                elif output_format == "csv":
                    fp = export_dir / "assignments_sem3.csv"
                    export_to_csv(assign_data, fp)
                else:
                    fp = export_dir / "assignments_sem3.md"
                    export_to_markdown(assign_data, fp, "Assignments Semester 3")
                exported_files.append(("Assignments Sem 3", len(assign_data)))
            except Exception as e:
                print_warning(f"Could not export semester 3 assignments: {e}")
            progress.update(task, advance=1, status="Sem 3 done")
            
            # Statistics
            try:
                stats = loader.load_statistics()
                if output_format == "json":
                    fp = export_dir / "statistics.json"
                    export_to_json(stats.model_dump(mode="json"), fp)
                else:
                    summary = [
                        {"Metric": "Sem 1 Assignments", "Value": stats.semester1.total_assignments},
                        {"Metric": "Sem 3 Assignments", "Value": stats.semester3.total_assignments},
                        {"Metric": "Total", "Value": stats.combined.total_assignments},
                    ]
                    if output_format == "csv":
                        fp = export_dir / "statistics.csv"
                        export_to_csv(summary, fp)
                    else:
                        fp = export_dir / "statistics.md"
                        export_to_markdown(summary, fp, "Statistics")
                exported_files.append(("Statistics", 1))
            except Exception as e:
                print_warning(f"Could not export statistics: {e}")
            progress.update(task, advance=1, status="Stats done")
            
            # Config
            try:
                config = loader.load_config()
                if output_format == "json":
                    fp = export_dir / "config.json"
                    export_to_json(config.model_dump(mode="json"), fp)
                exported_files.append(("Config", 1))
            except Exception as e:
                print_warning(f"Could not export config: {e}")
            progress.update(task, advance=1, status="Complete")
        
        # Summary
        console.print()
        print_success(f"Export complete! Files saved to: {export_dir}")
        console.print()
        
        table = Table(title="Export Summary", show_header=True)
        table.add_column("Data Type", style="cyan")
        table.add_column("Records", style="green", justify="right")
        for name, count in exported_files:
            table.add_row(name, str(count))
        console.print(table)
        
    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)
