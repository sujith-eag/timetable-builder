"""
Exception hierarchy for the timetable system.

This module defines a structured exception hierarchy that provides:
- Meaningful error messages for users
- Structured data for programmatic handling
- Context preservation for debugging
- Consistent error handling across the application

Exception Hierarchy:
    TimetableError (base)
    ├── ValidationError
    ├── DataLoadError
    ├── ConfigurationError
    ├── StageError
    └── SchedulingError
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional


class TimetableError(Exception):
    """
    Base exception for all timetable-related errors.

    All custom exceptions in the timetable system inherit from this class,
    allowing for catch-all exception handling when needed.

    Attributes:
        message: Human-readable error message
        details: Additional structured data about the error
    """

    def __init__(
        self,
        message: str,
        *,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Initialize TimetableError.

        Args:
            message: Human-readable error description
            details: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """Return string representation of the error."""
        return self.message

    def __repr__(self) -> str:
        """Return detailed representation of the error."""
        return f"{self.__class__.__name__}({self.message!r}, details={self.details!r})"

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(TimetableError):
    """
    Exception raised when data validation fails.

    This exception is raised when:
    - Required fields are missing
    - Field values are invalid
    - Data doesn't match expected schema
    - Cross-field validation fails

    Attributes:
        field: The field that failed validation (if applicable)
        value: The invalid value (if applicable)
    """

    def __init__(
        self,
        message: str,
        *,
        field: Optional[str] = None,
        value: Any = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Initialize ValidationError.

        Args:
            message: Description of the validation failure
            field: Name of the field that failed validation
            value: The invalid value
            details: Additional context
        """
        super().__init__(message, details=details)
        self.field = field
        self.value = value

    def __str__(self) -> str:
        """Return string representation with field context."""
        if self.field:
            return f"Validation error in '{self.field}': {self.message}"
        return f"Validation error: {self.message}"

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary."""
        result = super().to_dict()
        result.update({
            "field": self.field,
            "value": self.value if self.value is not None else None,
        })
        return result


class DataLoadError(TimetableError):
    """
    Exception raised when data loading fails.

    This exception is raised when:
    - File is not found
    - File cannot be read
    - JSON parsing fails
    - Required data files are missing

    Attributes:
        filepath: Path to the file that failed to load
    """

    def __init__(
        self,
        message: str,
        *,
        filepath: Optional[str | Path] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Initialize DataLoadError.

        Args:
            message: Description of the load failure
            filepath: Path to the file that failed to load
            details: Additional context
        """
        super().__init__(message, details=details)
        self.filepath = str(filepath) if filepath else None

    def __str__(self) -> str:
        """Return string representation with filepath context."""
        if self.filepath:
            return f"Data load error for '{self.filepath}': {self.message}"
        return f"Data load error: {self.message}"

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary."""
        result = super().to_dict()
        result["filepath"] = self.filepath
        return result


class ConfigurationError(TimetableError):
    """
    Exception raised when configuration is invalid.

    This exception is raised when:
    - Required configuration is missing
    - Configuration values are invalid
    - Environment variables are misconfigured
    - Settings file is malformed

    Attributes:
        config_key: The configuration key that caused the error
    """

    def __init__(
        self,
        message: str,
        *,
        config_key: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Initialize ConfigurationError.

        Args:
            message: Description of the configuration error
            config_key: The configuration key that caused the error
            details: Additional context
        """
        super().__init__(message, details=details)
        self.config_key = config_key

    def __str__(self) -> str:
        """Return string representation with config key context."""
        if self.config_key:
            return f"Configuration error for '{self.config_key}': {self.message}"
        return f"Configuration error: {self.message}"

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary."""
        result = super().to_dict()
        result["config_key"] = self.config_key
        return result


class StageError(TimetableError):
    """
    Exception raised when stage processing fails.

    This exception is raised when:
    - Stage build operation fails
    - Stage validation fails
    - Stage dependencies are not met
    - Stage output is invalid

    Attributes:
        stage: The stage number (1-6) where the error occurred
        operation: The operation that failed (e.g., 'build', 'validate')
    """

    def __init__(
        self,
        message: str,
        *,
        stage: Optional[int] = None,
        operation: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Initialize StageError.

        Args:
            message: Description of the stage error
            stage: Stage number where the error occurred
            operation: The operation that failed
            details: Additional context
        """
        super().__init__(message, details=details)
        self.stage = stage
        self.operation = operation

    def __str__(self) -> str:
        """Return string representation with stage context."""
        parts = []
        if self.stage:
            parts.append(f"Stage {self.stage}")
        if self.operation:
            parts.append(f"operation '{self.operation}'")
        if parts:
            return f"{' '.join(parts)}: {self.message}"
        return f"Stage error: {self.message}"

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary."""
        result = super().to_dict()
        result.update({
            "stage": self.stage,
            "operation": self.operation,
        })
        return result


class SchedulingError(TimetableError):
    """
    Exception raised when scheduling operations fail.

    This exception is raised when:
    - Scheduling constraints are violated
    - No valid schedule can be found
    - Session conflicts are detected
    - Resource capacity is exceeded

    Attributes:
        constraint: The constraint that was violated
        session_id: The session that caused the conflict
    """

    def __init__(
        self,
        message: str,
        *,
        constraint: Optional[str] = None,
        session_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Initialize SchedulingError.

        Args:
            message: Description of the scheduling error
            constraint: The constraint that was violated
            session_id: The session that caused the conflict
            details: Additional context
        """
        super().__init__(message, details=details)
        self.constraint = constraint
        self.session_id = session_id

    def __str__(self) -> str:
        """Return string representation with scheduling context."""
        parts = []
        if self.constraint:
            parts.append(f"constraint '{self.constraint}'")
        if self.session_id:
            parts.append(f"session '{self.session_id}'")
        if parts:
            return f"Scheduling error ({', '.join(parts)}): {self.message}"
        return f"Scheduling error: {self.message}"

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary."""
        result = super().to_dict()
        result.update({
            "constraint": self.constraint,
            "session_id": self.session_id,
        })
        return result


# Convenience aliases for common error patterns
FileNotFoundError = DataLoadError
InvalidDataError = ValidationError
