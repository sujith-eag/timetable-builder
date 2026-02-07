"""
JSON Schema validation utilities for timetable data.

This module provides utilities for validating JSON data against
JSON Schema files, independent of Pydantic model validation.

Usage:
    from timetable.core.schema import SchemaValidator

    validator = SchemaValidator()
    errors = validator.validate_file("stage_1/config.json", "config")
    if errors:
        for error in errors:
            print(f"Error: {error}")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional, Union

import jsonschema
from jsonschema import Draft7Validator, ValidationError as JsonSchemaValidationError

from timetable.core.exceptions import DataLoadError, ValidationError
from timetable.core.logging import get_logger

logger = get_logger(__name__)


class SchemaError:
    """Represents a single schema validation error."""

    def __init__(
        self,
        message: str,
        path: str,
        schema_path: str,
        value: Any = None,
    ):
        self.message = message
        self.path = path
        self.schema_path = schema_path
        self.value = value

    def __str__(self) -> str:
        if self.path:
            return f"[{self.path}] {self.message}"
        return self.message

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "message": self.message,
            "path": self.path,
            "schema_path": self.schema_path,
            "value": self.value,
        }


class SchemaValidator:
    """
    Validates JSON data against JSON Schema files.

    This validator uses JSON Schema Draft 7 and provides detailed
    error messages for validation failures.

    Attributes:
        schemas_dir: Directory containing schema files

    Example:
        >>> validator = SchemaValidator("/path/to/schemas")
        >>> errors = validator.validate("data.json", "stage1/config")
        >>> if errors:
        ...     for e in errors:
        ...         print(e)
    """

    # Mapping of schema names to file paths
    SCHEMA_MAP = {
        # Stage 1
        "config": "stage1/config.schema.json",
        "faculty": "stage1/faculty.schema.json",
        "subject": "stage1/subject.schema.json",
        # Stage 2
        "subjects_full": "stage2/subjects.schema.json",
        "faculty_full": "stage2/faculty.schema.json",
        # Stage 3
        "teaching_assignments": "stage3/teachingAssignments.schema.json",
        "overlap_constraints": "stage3/overlapConstraints.schema.json",
        "statistics": "stage3/statistics.schema.json",
    }

    def __init__(self, schemas_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the schema validator.

        Args:
            schemas_dir: Directory containing schema files.
                        If None, uses the package's schemas directory.
        """
        if schemas_dir:
            self.schemas_dir = Path(schemas_dir)
        else:
            # Default to package schemas directory
            self.schemas_dir = Path(__file__).parent.parent.parent.parent / "schemas"

        self._schema_cache: dict[str, dict] = {}
        logger.debug(f"Schema validator initialized with dir: {self.schemas_dir}")

    def get_schema(self, schema_name: str) -> dict[str, Any]:
        """
        Load a schema by name.

        Args:
            schema_name: Name of the schema (e.g., "config", "faculty_full")

        Returns:
            The loaded schema as a dictionary

        Raises:
            DataLoadError: If schema file cannot be loaded
        """
        if schema_name in self._schema_cache:
            return self._schema_cache[schema_name]

        # Get schema file path
        if schema_name in self.SCHEMA_MAP:
            schema_file = self.SCHEMA_MAP[schema_name]
        else:
            # Treat as direct file path
            schema_file = schema_name
            if not schema_file.endswith(".schema.json"):
                schema_file += ".schema.json"

        schema_path = self.schemas_dir / schema_file

        if not schema_path.exists():
            raise DataLoadError(
                f"Schema file not found: {schema_path}",
                filepath=schema_path,
                details={"schema_name": schema_name},
            )

        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
            self._schema_cache[schema_name] = schema
            logger.debug(f"Loaded schema: {schema_name}")
            return schema
        except json.JSONDecodeError as e:
            raise DataLoadError(
                f"Invalid JSON in schema file: {e}",
                filepath=schema_path,
            ) from e

    def validate_data(
        self,
        data: dict[str, Any],
        schema_name: str,
    ) -> list[SchemaError]:
        """
        Validate data against a schema.

        Args:
            data: The data to validate
            schema_name: Name of the schema to validate against

        Returns:
            List of validation errors (empty if valid)
        """
        schema = self.get_schema(schema_name)
        validator = Draft7Validator(schema)
        errors = []

        for error in sorted(validator.iter_errors(data), key=lambda e: e.path):
            path = ".".join(str(p) for p in error.absolute_path)
            schema_path = ".".join(str(p) for p in error.schema_path)

            errors.append(
                SchemaError(
                    message=error.message,
                    path=path,
                    schema_path=schema_path,
                    value=error.instance if not isinstance(error.instance, dict) else None,
                )
            )

        return errors

    def validate_file(
        self,
        filepath: Union[str, Path],
        schema_name: str,
    ) -> list[SchemaError]:
        """
        Validate a JSON file against a schema.

        Args:
            filepath: Path to the JSON file to validate
            schema_name: Name of the schema to validate against

        Returns:
            List of validation errors (empty if valid)

        Raises:
            DataLoadError: If file cannot be read
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise DataLoadError(
                f"File not found: {filepath}",
                filepath=filepath,
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise DataLoadError(
                f"Invalid JSON syntax: {e}",
                filepath=filepath,
            ) from e

        return self.validate_data(data, schema_name)

    def is_valid(
        self,
        data: dict[str, Any],
        schema_name: str,
    ) -> bool:
        """
        Check if data is valid against a schema.

        Args:
            data: The data to validate
            schema_name: Name of the schema

        Returns:
            True if valid, False otherwise
        """
        errors = self.validate_data(data, schema_name)
        return len(errors) == 0

    def is_file_valid(
        self,
        filepath: Union[str, Path],
        schema_name: str,
    ) -> bool:
        """
        Check if a JSON file is valid against a schema.

        Args:
            filepath: Path to the JSON file
            schema_name: Name of the schema

        Returns:
            True if valid, False otherwise
        """
        try:
            errors = self.validate_file(filepath, schema_name)
            return len(errors) == 0
        except DataLoadError:
            return False

    def list_schemas(self) -> list[str]:
        """
        List available schema names.

        Returns:
            List of schema names that can be used for validation
        """
        return list(self.SCHEMA_MAP.keys())

    def clear_cache(self) -> None:
        """Clear the schema cache."""
        self._schema_cache.clear()
        logger.debug("Schema cache cleared")


# Module-level convenience functions


def validate_json(
    data: dict[str, Any],
    schema_name: str,
    schemas_dir: Optional[Union[str, Path]] = None,
) -> list[SchemaError]:
    """
    Validate JSON data against a schema.

    Args:
        data: The data to validate
        schema_name: Name of the schema
        schemas_dir: Optional path to schemas directory

    Returns:
        List of validation errors
    """
    validator = SchemaValidator(schemas_dir)
    return validator.validate_data(data, schema_name)


def validate_json_file(
    filepath: Union[str, Path],
    schema_name: str,
    schemas_dir: Optional[Union[str, Path]] = None,
) -> list[SchemaError]:
    """
    Validate a JSON file against a schema.

    Args:
        filepath: Path to the JSON file
        schema_name: Name of the schema
        schemas_dir: Optional path to schemas directory

    Returns:
        List of validation errors
    """
    validator = SchemaValidator(schemas_dir)
    return validator.validate_file(filepath, schema_name)
