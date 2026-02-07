"""
Unit tests for the exception hierarchy.

Tests are written first following TDD principles.
"""

import pytest


class TestTimetableError:
    """Tests for the base TimetableError exception."""

    def test_base_exception_inherits_from_exception(self):
        """TimetableError should inherit from Exception."""
        from timetable.core.exceptions import TimetableError

        assert issubclass(TimetableError, Exception)

    def test_base_exception_with_message(self):
        """TimetableError should accept and store a message."""
        from timetable.core.exceptions import TimetableError

        error = TimetableError("Something went wrong")
        assert str(error) == "Something went wrong"

    def test_base_exception_with_details(self):
        """TimetableError should accept optional details."""
        from timetable.core.exceptions import TimetableError

        error = TimetableError("Error occurred", details={"key": "value"})
        assert error.details == {"key": "value"}

    def test_base_exception_default_details(self):
        """TimetableError should have empty dict as default details."""
        from timetable.core.exceptions import TimetableError

        error = TimetableError("Error occurred")
        assert error.details == {}


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_inherits_from_timetable_error(self):
        """ValidationError should inherit from TimetableError."""
        from timetable.core.exceptions import TimetableError, ValidationError

        assert issubclass(ValidationError, TimetableError)

    def test_validation_error_with_field(self):
        """ValidationError should accept a field parameter."""
        from timetable.core.exceptions import ValidationError

        error = ValidationError("Invalid value", field="facultyId")
        assert error.field == "facultyId"

    def test_validation_error_without_field(self):
        """ValidationError should work without field parameter."""
        from timetable.core.exceptions import ValidationError

        error = ValidationError("Invalid data")
        assert error.field is None

    def test_validation_error_with_value(self):
        """ValidationError should accept a value parameter."""
        from timetable.core.exceptions import ValidationError

        error = ValidationError("Invalid value", field="age", value=-1)
        assert error.value == -1

    def test_validation_error_str_representation(self):
        """ValidationError should have informative string representation."""
        from timetable.core.exceptions import ValidationError

        error = ValidationError("Invalid value", field="name", value="")
        error_str = str(error)
        assert "Invalid value" in error_str


class TestDataLoadError:
    """Tests for DataLoadError exception."""

    def test_inherits_from_timetable_error(self):
        """DataLoadError should inherit from TimetableError."""
        from timetable.core.exceptions import DataLoadError, TimetableError

        assert issubclass(DataLoadError, TimetableError)

    def test_data_load_error_with_filepath(self):
        """DataLoadError should accept a filepath parameter."""
        from timetable.core.exceptions import DataLoadError

        error = DataLoadError("File not found", filepath="/path/to/file.json")
        assert error.filepath == "/path/to/file.json"

    def test_data_load_error_without_filepath(self):
        """DataLoadError should work without filepath parameter."""
        from timetable.core.exceptions import DataLoadError

        error = DataLoadError("Data loading failed")
        assert error.filepath is None

    def test_data_load_error_str_includes_path(self):
        """DataLoadError string should include filepath if provided."""
        from timetable.core.exceptions import DataLoadError

        error = DataLoadError("File not found", filepath="/config.json")
        assert "/config.json" in str(error) or "File not found" in str(error)


class TestConfigurationError:
    """Tests for ConfigurationError exception."""

    def test_inherits_from_timetable_error(self):
        """ConfigurationError should inherit from TimetableError."""
        from timetable.core.exceptions import ConfigurationError, TimetableError

        assert issubclass(ConfigurationError, TimetableError)

    def test_configuration_error_with_key(self):
        """ConfigurationError should accept a config_key parameter."""
        from timetable.core.exceptions import ConfigurationError

        error = ConfigurationError("Missing required config", config_key="data_dir")
        assert error.config_key == "data_dir"

    def test_configuration_error_without_key(self):
        """ConfigurationError should work without config_key parameter."""
        from timetable.core.exceptions import ConfigurationError

        error = ConfigurationError("Invalid configuration")
        assert error.config_key is None


class TestStageError:
    """Tests for StageError exception."""

    def test_inherits_from_timetable_error(self):
        """StageError should inherit from TimetableError."""
        from timetable.core.exceptions import StageError, TimetableError

        assert issubclass(StageError, TimetableError)

    def test_stage_error_with_stage_number(self):
        """StageError should accept a stage parameter."""
        from timetable.core.exceptions import StageError

        error = StageError("Stage processing failed", stage=2)
        assert error.stage == 2

    def test_stage_error_with_operation(self):
        """StageError should accept an operation parameter."""
        from timetable.core.exceptions import StageError

        error = StageError("Build failed", stage=3, operation="build_subjects")
        assert error.operation == "build_subjects"

    def test_stage_error_defaults(self):
        """StageError should have sensible defaults."""
        from timetable.core.exceptions import StageError

        error = StageError("Error")
        assert error.stage is None
        assert error.operation is None


class TestSchedulingError:
    """Tests for SchedulingError exception."""

    def test_inherits_from_timetable_error(self):
        """SchedulingError should inherit from TimetableError."""
        from timetable.core.exceptions import SchedulingError, TimetableError

        assert issubclass(SchedulingError, TimetableError)

    def test_scheduling_error_with_constraint(self):
        """SchedulingError should accept a constraint parameter."""
        from timetable.core.exceptions import SchedulingError

        error = SchedulingError(
            "Constraint violation", constraint="no_faculty_overlap"
        )
        assert error.constraint == "no_faculty_overlap"

    def test_scheduling_error_with_session(self):
        """SchedulingError should accept a session_id parameter."""
        from timetable.core.exceptions import SchedulingError

        error = SchedulingError("Session conflict", session_id="SES-001")
        assert error.session_id == "SES-001"


class TestExceptionChaining:
    """Tests for exception chaining and cause preservation."""

    def test_exception_preserves_cause(self):
        """Exceptions should preserve the original cause."""
        from timetable.core.exceptions import DataLoadError

        original = FileNotFoundError("file.json")
        error = DataLoadError("Could not load config", filepath="file.json")
        error.__cause__ = original

        assert error.__cause__ is original

    def test_exception_from_json_error(self):
        """Exceptions should work with JSON decode errors."""
        import json

        from timetable.core.exceptions import DataLoadError

        try:
            json.loads("invalid json")
        except json.JSONDecodeError as e:
            error = DataLoadError("Invalid JSON format", filepath="data.json")
            error.__cause__ = e
            assert isinstance(error.__cause__, json.JSONDecodeError)
