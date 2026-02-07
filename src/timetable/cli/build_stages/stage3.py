"""
Stage 3 build functionality.
"""

from pathlib import Path
from typing import List, Tuple, Optional

from timetable.core.loader import DataLoader
from timetable.core.exceptions import TimetableError
from . import run_script, get_scripts_dir


def build_stage3(data_path: Path, validate: bool = True, reports: bool = True, verbose: bool = False) -> List[Tuple[str, bool, str]]:
    """
    Build Stage 3 data from Stage 2 inputs.

    Generates:
    - teachingAssignments_sem1.json
    - teachingAssignments_sem3.json
    - studentGroupOverlapConstraints.json
    - statistics.json
    - reports/ (markdown reports)

    Args:
        data_path: Path to the data directory
        validate: Whether to run validation after building
        reports: Whether to generate reports
        verbose: Whether to show detailed output

    Returns:
        List of (description, success, output) tuples
    """
    scripts_dir = get_scripts_dir(3)

    if not scripts_dir.exists():
        return [("Stage 3 scripts", False, f"Scripts directory not found: {scripts_dir}")]

    results = []

    # Check prerequisites
    loader = DataLoader(data_path)
    try:
        faculty = loader.load_faculty_full()
        subjects = loader.load_subjects_full()
        results.append(("Prerequisites check", True, f"Stage 2 data found: {len(subjects)} subjects, {len(faculty)} faculty"))
    except TimetableError as e:
        results.append(("Prerequisites check", False, f"Stage 2 data not found or invalid: {e}"))
        return results

    build_scripts = [
        ("generate_overlap_matrix.py", "Generating overlap constraints"),
        ("build_assignments_sem3.py", "Building Semester 3 assignments"),
        ("build_assignments_sem1.py", "Building Semester 1 assignments"),
    ]

    if validate:
        build_scripts.append(("validate_stage3.py", "Validating assignments"))

    build_scripts.append(("generate_statistics.py", "Generating statistics"))

    if reports:
        build_scripts.append(("generate_reports.py", "Generating reports"))

    for script_name, description in build_scripts:
        script_path = scripts_dir / script_name

        if not script_path.exists():
            results.append((description, False, f"Script not found: {script_path}"))
            continue

        success, output = run_script(script_path, data_path, description)
        results.append((description, success, output))

    return results


def get_stage3_scripts() -> List[str]:
    """Return list of scripts for Stage 3."""
    return [
        "generate_overlap_matrix.py",
        "build_assignments_sem3.py",
        "build_assignments_sem1.py",
        "validate_stage3.py",
        "generate_statistics.py",
        "generate_reports.py",
    ]