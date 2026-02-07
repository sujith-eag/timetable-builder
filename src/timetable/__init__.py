"""
Timetable Generation System

A comprehensive academic timetable generation and management system.
"""

__version__ = "0.1.0"
__author__ = "Eagle Campus"
__description__ = "Academic Timetable Generation System"

from timetable.config.settings import get_settings
from timetable.core.exceptions import TimetableError

__all__ = [
    "__version__",
    "get_settings",
    "TimetableError",
]
