"""
Shared utilities for build stages.
"""

from pathlib import Path
import subprocess
import sys
from typing import Tuple


def run_script(script_path: Path, data_path: Path, description: str) -> Tuple[bool, str]:
    """Run a build script and return (success, output)."""
    try:
        cmd = [sys.executable, str(script_path), "--data-dir", str(data_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=script_path.parent)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, f"Error: {str(e)}"


def get_scripts_dir(stage: int) -> Path:
    """Get scripts directory for a stage."""
    import timetable
    return Path(timetable.__file__).parent / "scripts" / f"stage{stage}"