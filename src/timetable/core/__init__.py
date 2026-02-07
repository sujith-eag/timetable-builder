"""
Core functionality for the timetable system.

This module contains shared utilities, exceptions, and base classes.
"""

from timetable.core.exceptions import (
    ConfigurationError,
    DataLoadError,
    SchedulingError,
    StageError,
    TimetableError,
    ValidationError,
)
from timetable.core.loader import (
    DataLoader,
    load_and_validate,
    load_config,
    load_faculty,
    load_json,
    load_room_preferences,
    load_student_groups,
    load_subjects,
    validate_model,
)
from timetable.core.logging import get_logger, setup_logging

__all__ = [
    # Exceptions
    "TimetableError",
    "ValidationError",
    "DataLoadError",
    "ConfigurationError",
    "StageError",
    "SchedulingError",
    # Logging
    "get_logger",
    "setup_logging",
    # Loader
    "DataLoader",
    "load_json",
    "load_and_validate",
    "validate_model",
    "load_config",
    "load_faculty",
    "load_subjects",
    "load_student_groups",
    "load_room_preferences",
]
