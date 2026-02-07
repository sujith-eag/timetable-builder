"""
Structured logging for the timetable system.

This module provides:
- Consistent log formatting across the application
- Console and file logging handlers
- Log level configuration
- Rich console output support (when available)
- JSON structured logging for production

Usage:
    from timetable.core.logging import get_logger, setup_logging

    # Setup at application start
    setup_logging(level="DEBUG")

    # Get a logger in any module
    logger = get_logger(__name__)
    logger.info("Processing stage 2")
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

# Try to import rich for pretty console output
try:
    from rich.logging import RichHandler

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# Default format for log messages
DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Package logger name
PACKAGE_NAME = "timetable"

# Track if logging has been set up
_logging_configured = False


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for the specified module.

    If no name is provided, returns the root timetable logger.
    All loggers are children of the 'timetable' logger.

    Args:
        name: Module name for the logger. If None, uses the package name.

    Returns:
        A configured Logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Starting process")
    """
    if name is None:
        return logging.getLogger(PACKAGE_NAME)

    # Ensure all loggers are under the timetable namespace
    if not name.startswith(PACKAGE_NAME):
        name = f"{PACKAGE_NAME}.{name}"

    return logging.getLogger(name)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path | str] = None,
    format_string: Optional[str] = None,
    use_rich: bool = True,
) -> None:
    """
    Configure logging for the application.

    This function sets up the root timetable logger with appropriate
    handlers and formatters. Should be called once at application startup.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. If provided, logs are written to file.
        format_string: Custom format string for log messages
        use_rich: Use rich handler for pretty console output (if available)

    Raises:
        ValueError: If level is not a valid log level

    Example:
        >>> setup_logging(level="DEBUG", log_file="/var/log/timetable.log")
    """
    global _logging_configured

    # Validate log level
    level = level.upper()
    numeric_level = getattr(logging, level, None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")

    # Get the root timetable logger
    logger = logging.getLogger(PACKAGE_NAME)
    logger.setLevel(numeric_level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Determine format
    log_format = format_string or DEFAULT_FORMAT

    # Add console handler
    if use_rich and RICH_AVAILABLE:
        console_handler = RichHandler(
            level=numeric_level,
            show_time=True,
            show_path=True,
            rich_tracebacks=True,
        )
    else:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(numeric_level)
        console_formatter = logging.Formatter(log_format, datefmt=DEFAULT_DATE_FORMAT)
        console_handler.setFormatter(console_formatter)

    logger.addHandler(console_handler)

    # Add file handler if path provided
    if log_file:
        log_path = Path(log_file)
        # Create parent directory if needed
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_formatter = logging.Formatter(log_format, datefmt=DEFAULT_DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Don't propagate to root logger
    logger.propagate = False

    _logging_configured = True

    # Log initial message
    logger.debug(f"Logging configured: level={level}, file={log_file}")


def configure_from_settings() -> None:
    """
    Configure logging from application settings.

    This function reads the settings and configures logging accordingly.
    Should be called after settings are loaded.
    """
    from timetable.config.settings import get_settings

    settings = get_settings()
    setup_logging(
        level=settings.log_level,
        log_file=settings.log_file,
        format_string=settings.log_format,
    )


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds context to log messages.

    Useful for adding consistent context like stage number or operation name.

    Example:
        >>> logger = get_logger(__name__)
        >>> stage_logger = LoggerAdapter(logger, {"stage": 2})
        >>> stage_logger.info("Building subjects")  # Includes stage=2 context
    """

    def process(
        self, msg: str, kwargs: dict
    ) -> tuple[str, dict]:
        """Add extra context to the log message."""
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


def get_stage_logger(stage: int) -> LoggerAdapter:
    """
    Get a logger configured for a specific stage.

    Args:
        stage: Stage number (1-6)

    Returns:
        LoggerAdapter with stage context

    Example:
        >>> logger = get_stage_logger(2)
        >>> logger.info("Processing subjects")
    """
    base_logger = get_logger(f"stage{stage}")
    return LoggerAdapter(base_logger, {"stage": stage})
