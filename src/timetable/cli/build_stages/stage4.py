"""
Stage 4 build functionality.
"""

from pathlib import Path
from typing import List, Tuple, Optional

from timetable.core.loader import DataLoader
from timetable.core.exceptions import TimetableError
from . import run_script, get_scripts_dir


def build_stage4(data_path: Path, validate: bool = False, verbose: bool = False) -> List[Tuple[str, bool, str]]:
    """
    Build Stage 4 data from Stage 3 inputs.

    Generates:
    - schedulingInput.json (complete input for AI solver)

    Args:
        data_path: Path to the data directory
        validate: Whether to run validation after building
        verbose: Whether to show detailed output

    Returns:
        List of (description, success, output) tuples
    """
    scripts_dir = get_scripts_dir(4)

    if not scripts_dir.exists():
        return [("Stage 4 scripts", False, f"Scripts directory not found: {scripts_dir}")]

    results = []

    # Check prerequisites
    loader = DataLoader(data_path)
    try:
        assignments1 = loader.load_teaching_assignments(semester=1)
        assignments3 = loader.load_teaching_assignments(semester=3)
        overlap = loader.load_overlap_constraints()
        results.append(("Prerequisites check", True, f"Stage 3 data found: {len(assignments1.assignments)} sem1, {len(assignments3.assignments)} sem3 assignments"))
    except TimetableError as e:
        results.append(("Prerequisites check", False, f"Stage 3 data not found or invalid: {e}"))
        return results

    build_scripts = [
        ("build_scheduling_input.py", "Building scheduling input for AI solver"),
    ]

    if validate:
        build_scripts.append(("validate_stage4.py", "Validating Stage 4 data"))

    # Run build scripts
    for script_name, description in build_scripts:
        script_path = scripts_dir / script_name

        if not script_path.exists():
            results.append((description, False, f"Script not found: {script_path}"))
            continue

        success, output = run_script(script_path, data_path, description)
        results.append((description, success, output))

    return results