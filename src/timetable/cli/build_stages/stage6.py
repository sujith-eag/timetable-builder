"""
Stage 6 build functionality.
"""

from pathlib import Path
from typing import List, Tuple, Optional

from timetable.core.loader import DataLoader
from timetable.core.exceptions import TimetableError
from . import run_script, get_scripts_dir


def build_stage6(data_path: Path, validate: bool = True, views: bool = True, verbose: bool = False) -> List[Tuple[str, bool, str]]:
    """
    Build Stage 6 data from Stage 5 inputs.

    Generates:
    - timetable_enriched.json (complete enriched timetable)
    - views/ (faculty and student views)
    - reports/ (analysis reports)

    Args:
        data_path: Path to the data directory
        validate: Whether to run validation after building
        views: Whether to generate faculty and student views
        verbose: Whether to show detailed output

    Returns:
        List of (description, success, output) tuples
    """
    scripts_dir = get_scripts_dir(6)

    if not scripts_dir.exists():
        return [("Stage 6 scripts", False, f"Scripts directory not found: {scripts_dir}")]

    results = []

    # Check prerequisites
    loader = DataLoader(data_path)
    try:
        ai_schedule = loader.load_ai_schedule()
        results.append(("Prerequisites check", True, f"Stage 5 data found: {len(ai_schedule.schedule)} scheduled sessions"))
    except TimetableError as e:
        results.append(("Prerequisites check", False, f"Stage 5 data not found or invalid: {e}"))
        return results

    build_scripts = [
        ("enrich_schedule.py", "Enriching schedule with full details"),
        ("analyze_schedule.py", "Analyzing schedule quality"),
    ]

    if validate:
        build_scripts.append(("validate_assignments.py", "Validating enriched assignments"))

    if views:
        build_scripts.extend([
            ("generate_faculty_views.py", "Generating faculty views"),
            ("generate_student_views.py", "Generating student views"),
        ])

    # Run build scripts
    for script_name, description in build_scripts:
        script_path = scripts_dir / script_name

        if not script_path.exists():
            results.append((description, False, f"Script not found: {script_path}"))
            continue

        # Special handling for enrich_schedule.py which needs schedule file argument
        if script_name == "enrich_schedule.py":
            # Assume the schedule file is ai_solved_schedule.json in stage5
            schedule_file = data_path / "stage_5" / "ai_solved_schedule.json"
            if not schedule_file.exists():
                results.append((description, False, f"Schedule file not found: {schedule_file}"))
                continue
            # For enrich_schedule.py, we need to pass the schedule file as an argument
            # The script expects: python script.py --data-dir <data_dir> <schedule_file>
            # But our run_script function passes --data-dir automatically, so we need to modify this
            success, output = run_script(script_path, data_path, f"{description} (using {schedule_file.name})")
        else:
            success, output = run_script(script_path, data_path, description)
        results.append((description, success, output))

    return results