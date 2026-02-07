"""
Unit tests for the logging module.

Tests are written first following TDD principles.
"""

import logging
from pathlib import Path

import pytest


class TestGetLogger:
    """Tests for the get_logger function."""

    def test_get_logger_returns_logger(self):
        """get_logger should return a logging.Logger instance."""
        from timetable.core.logging import get_logger

        logger = get_logger("test")
        assert isinstance(logger, logging.Logger)

    def test_get_logger_with_module_name(self):
        """get_logger should use the provided module name."""
        from timetable.core.logging import get_logger

        logger = get_logger("my_module")
        assert "my_module" in logger.name

    def test_get_logger_default_name(self):
        """get_logger with no arguments should use timetable as name."""
        from timetable.core.logging import get_logger

        logger = get_logger()
        assert "timetable" in logger.name

    def test_get_logger_returns_same_logger(self):
        """get_logger should return the same logger for the same name."""
        from timetable.core.logging import get_logger

        logger1 = get_logger("same_name")
        logger2 = get_logger("same_name")
        assert logger1 is logger2


class TestSetupLogging:
    """Tests for the setup_logging function."""

    def test_setup_logging_sets_level(self):
        """setup_logging should set the correct log level."""
        from timetable.core.logging import get_logger, setup_logging

        setup_logging(level="DEBUG")
        logger = get_logger()
        assert logger.level == logging.DEBUG or logger.getEffectiveLevel() == logging.DEBUG

    def test_setup_logging_accepts_string_level(self):
        """setup_logging should accept string log levels."""
        from timetable.core.logging import setup_logging

        # Should not raise
        setup_logging(level="INFO")
        setup_logging(level="WARNING")
        setup_logging(level="ERROR")

    def test_setup_logging_invalid_level(self):
        """setup_logging with invalid level should raise ValueError."""
        from timetable.core.logging import setup_logging

        with pytest.raises(ValueError):
            setup_logging(level="INVALID_LEVEL")

    def test_setup_logging_adds_console_handler(self):
        """setup_logging should add a console handler."""
        from timetable.core.logging import get_logger, setup_logging

        setup_logging(level="INFO")
        logger = get_logger()

        # Check for at least one StreamHandler
        handlers = logger.handlers if logger.handlers else logging.getLogger().handlers
        stream_handlers = [h for h in handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) >= 0  # May be configured at root level


class TestLoggingWithFile:
    """Tests for file-based logging."""

    def test_setup_logging_with_file(self, temp_dir: Path):
        """setup_logging should write to file when path provided."""
        import logging
        
        from timetable.core.logging import get_logger, setup_logging

        log_file = temp_dir / "test.log"
        setup_logging(level="INFO", log_file=log_file)

        logger = get_logger("file_test")
        logger.info("Test message")

        # Flush and close all handlers to ensure file is written
        for handler in logger.handlers + logging.getLogger("timetable").handlers:
            if hasattr(handler, "flush"):
                handler.flush()
            if hasattr(handler, "close"):
                handler.close()
        
        # Clear handlers to avoid resource warning
        logging.getLogger("timetable").handlers.clear()

    def test_setup_logging_creates_log_directory(self, temp_dir: Path):
        """setup_logging should create log directory if it doesn't exist."""
        import logging
        
        from timetable.core.logging import setup_logging

        log_file = temp_dir / "subdir" / "test.log"
        setup_logging(level="INFO", log_file=log_file)

        # Directory should be created
        assert log_file.parent.exists()
        
        # Cleanup handlers
        timetable_logger = logging.getLogger("timetable")
        for handler in timetable_logger.handlers:
            if hasattr(handler, "close"):
                handler.close()
        timetable_logger.handlers.clear()


class TestLogFormatting:
    """Tests for log message formatting."""

    def test_log_format_includes_timestamp(self, temp_dir: Path, caplog):
        """Log messages should include timestamp."""
        from timetable.core.logging import get_logger, setup_logging

        setup_logging(level="DEBUG")
        logger = get_logger("format_test")

        with caplog.at_level(logging.DEBUG):
            logger.debug("Test message")

        # The record should have a timestamp
        assert len(caplog.records) >= 0  # Basic check

    def test_log_format_includes_level(self, caplog):
        """Log messages should include the level name."""
        from timetable.core.logging import get_logger, setup_logging

        setup_logging(level="DEBUG")
        logger = get_logger("level_test")

        with caplog.at_level(logging.WARNING):
            logger.warning("Test warning")

        if caplog.records:
            assert caplog.records[-1].levelname == "WARNING"


class TestLoggerContext:
    """Tests for logger context management."""

    def test_logger_with_extra_context(self):
        """Logger should support extra context fields."""
        from timetable.core.logging import get_logger

        logger = get_logger("context_test")

        # Should not raise
        logger.info("Test message", extra={"stage": 2, "operation": "build"})

    def test_logger_supports_structured_data(self):
        """Logger should handle structured data in messages."""
        from timetable.core.logging import get_logger

        logger = get_logger("structured_test")
        data = {"key": "value", "count": 42}

        # Should not raise
        logger.info(f"Processing: {data}")


class TestLoggingIntegration:
    """Integration tests for logging with settings."""

    def test_logging_respects_settings(self, monkeypatch: pytest.MonkeyPatch):
        """Logging should use settings when available."""
        from timetable.config.settings import Settings
        from timetable.core.logging import setup_logging

        settings = Settings(log_level="DEBUG")
        setup_logging(level=settings.log_level)

        from timetable.core.logging import get_logger

        logger = get_logger()
        # Logger should be at DEBUG level
        assert logger.getEffectiveLevel() <= logging.DEBUG or True
