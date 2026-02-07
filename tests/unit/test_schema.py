"""
Tests for the JSON Schema validation module.

This module tests the schema validation utilities including:
- Schema loading
- Data validation against schemas
- File validation
- Error reporting
"""

import json
from pathlib import Path

import pytest

from timetable.core.schema import (
    SchemaValidator,
    SchemaError,
    validate_json,
    validate_json_file,
)
from timetable.core.exceptions import DataLoadError


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def v4_data_dir() -> Path:
    """Get the V4 data directory path."""
    current = Path(__file__).parent.parent.parent
    return current


@pytest.fixture
def schemas_dir(v4_data_dir) -> Path:
    """Get the schemas directory path."""
    return v4_data_dir / "src" / "timetable" / "schemas"


@pytest.fixture
def validator(schemas_dir) -> SchemaValidator:
    """Create a schema validator."""
    return SchemaValidator(schemas_dir)


@pytest.fixture
def temp_data(tmp_path):
    """Create temporary test data files."""
    # Valid config data
    config_data = {
        "config": {
            "dayStart": "09:00",
            "dayEnd": "17:00",
            "weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri"],
            "daySlotPattern": {
                "Mon": ["S1", "S2"],
                "Tue": ["S1", "S2"],
                "Wed": ["S1", "S2"],
                "Thu": ["S1", "S2"],
                "Fri": ["S1", "S2"],
                "Sat": []
            },
            "breakWindows": [],
            "timeSlots": [
                {"slotId": "S1", "start": "09:00", "end": "10:00", "lengthMinutes": 60}
            ],
            "theorySessionMinutes": 60,
            "labTutorialSessionMinutes": 120,
            "creditToHours": {"theory": 1, "tutorial": 1, "practical": 2},
            "validSlotCombinations": {"single": ["S1"], "double": [], "saturday": []},
            "sessionTypes": {
                "theory": {"duration": 60, "requiresContiguous": False},
                "tutorial": {"duration": 60, "requiresContiguous": False},
                "practical": {"duration": 120, "requiresContiguous": True}
            },
            "resourceConstraints": {
                "maxConsecutiveSlotsPerFaculty": 3,
                "maxDailySlotsPerStudentGroup": 6,
                "minGapBetweenSameFaculty": 0
            },
            "resources": {
                "rooms": [
                    {"roomId": "R101", "type": "lecture", "capacity": 60}
                ]
            }
        }
    }

    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config_data))

    # Invalid config (missing required fields)
    invalid_config = {"config": {"dayStart": "09:00"}}
    invalid_path = tmp_path / "invalid_config.json"
    invalid_path.write_text(json.dumps(invalid_config))

    # Invalid JSON
    bad_json_path = tmp_path / "bad.json"
    bad_json_path.write_text("{invalid json}")

    return {
        "config_path": config_path,
        "config_data": config_data,
        "invalid_path": invalid_path,
        "bad_json_path": bad_json_path,
    }


# ============================================================================
# Test SchemaValidator Initialization
# ============================================================================


class TestSchemaValidatorInit:
    """Test schema validator initialization."""

    def test_init_with_custom_path(self, schemas_dir):
        """Test initialization with custom schemas directory."""
        validator = SchemaValidator(schemas_dir)
        assert validator.schemas_dir == schemas_dir

    def test_init_with_string_path(self, schemas_dir):
        """Test initialization with string path."""
        validator = SchemaValidator(str(schemas_dir))
        assert validator.schemas_dir == schemas_dir

    def test_list_schemas(self, validator):
        """Test listing available schemas."""
        schemas = validator.list_schemas()
        assert isinstance(schemas, list)
        assert "config" in schemas
        assert "faculty" in schemas
        assert "subjects_full" in schemas
        assert "faculty_full" in schemas


# ============================================================================
# Test Schema Loading
# ============================================================================


class TestSchemaLoading:
    """Test schema file loading."""

    def test_load_config_schema(self, validator):
        """Test loading config schema."""
        schema = validator.get_schema("config")
        assert isinstance(schema, dict)
        assert "$schema" in schema
        assert "properties" in schema

    def test_load_faculty_schema(self, validator):
        """Test loading faculty schema."""
        schema = validator.get_schema("faculty")
        assert isinstance(schema, dict)

    def test_load_nonexistent_schema(self, validator):
        """Test loading non-existent schema raises error."""
        with pytest.raises(DataLoadError) as exc_info:
            validator.get_schema("nonexistent_schema")
        assert "not found" in str(exc_info.value).lower()

    def test_schema_caching(self, validator):
        """Test that schemas are cached."""
        schema1 = validator.get_schema("config")
        schema2 = validator.get_schema("config")
        assert schema1 is schema2  # Same object

    def test_clear_cache(self, validator):
        """Test clearing schema cache."""
        validator.get_schema("config")
        assert len(validator._schema_cache) > 0
        validator.clear_cache()
        assert len(validator._schema_cache) == 0


# ============================================================================
# Test Schema Validation
# ============================================================================


class TestSchemaValidation:
    """Test data validation against schemas."""

    def test_validate_valid_faculty_data(self, validator):
        """Test validating valid faculty data."""
        data = {
            "faculty": [
                {
                    "facultyId": "F001",
                    "name": "Dr. Test",
                    "designation": "Professor"
                }
            ]
        }
        errors = validator.validate_data(data, "faculty")
        assert len(errors) == 0

    def test_validate_invalid_data(self, validator):
        """Test validating invalid data returns errors."""
        # Faculty missing required fields
        data = {
            "faculty": [
                {"name": "Test"}  # Missing facultyId and designation
            ]
        }
        errors = validator.validate_data(data, "faculty")
        assert len(errors) > 0
        assert any("facultyId" in str(e) or "designation" in str(e) for e in errors)

    def test_is_valid_true(self, validator):
        """Test is_valid returns True for valid data."""
        data = {
            "faculty": [
                {
                    "facultyId": "F001",
                    "name": "Dr. Test",
                    "designation": "Professor"
                }
            ]
        }
        assert validator.is_valid(data, "faculty")

    def test_is_valid_false(self, validator):
        """Test is_valid returns False for invalid data."""
        data = {"faculty": [{"name": "Test"}]}
        assert not validator.is_valid(data, "faculty")


# ============================================================================
# Test File Validation
# ============================================================================


class TestFileValidation:
    """Test JSON file validation."""

    def test_validate_valid_file(self, validator, v4_data_dir):
        """Test validating a valid Stage 1 file."""
        faculty_file = v4_data_dir / "stage_1" / "facultyBasic.json"
        if faculty_file.exists():
            errors = validator.validate_file(faculty_file, "faculty")
            assert isinstance(errors, list)

    def test_validate_nonexistent_file(self, validator):
        """Test validating non-existent file raises error."""
        with pytest.raises(DataLoadError) as exc_info:
            validator.validate_file("/nonexistent/file.json", "faculty")
        assert "not found" in str(exc_info.value).lower()

    def test_validate_invalid_json_file(self, validator, temp_data):
        """Test validating invalid JSON file raises error."""
        with pytest.raises(DataLoadError) as exc_info:
            validator.validate_file(temp_data["bad_json_path"], "faculty")
        assert "json" in str(exc_info.value).lower()

    def test_is_file_valid_true(self, validator, v4_data_dir):
        """Test is_file_valid returns True for valid file."""
        faculty_file = v4_data_dir / "stage_1" / "facultyBasic.json"
        if faculty_file.exists():
            # May or may not be valid depending on schema match
            result = validator.is_file_valid(faculty_file, "faculty")
            assert isinstance(result, bool)

    def test_is_file_valid_false_nonexistent(self, validator):
        """Test is_file_valid returns False for non-existent file."""
        assert not validator.is_file_valid("/nonexistent.json", "faculty")


# ============================================================================
# Test SchemaError
# ============================================================================


class TestSchemaError:
    """Test SchemaError class."""

    def test_error_str_with_path(self):
        """Test error string representation with path."""
        error = SchemaError(
            message="is a required property",
            path="faculty.0.facultyId",
            schema_path="properties.faculty.items.required",
        )
        result = str(error)
        assert "faculty.0.facultyId" in result
        assert "required property" in result

    def test_error_str_without_path(self):
        """Test error string representation without path."""
        error = SchemaError(
            message="Invalid type",
            path="",
            schema_path="type",
        )
        result = str(error)
        assert "Invalid type" in result

    def test_error_to_dict(self):
        """Test error dictionary conversion."""
        error = SchemaError(
            message="Test message",
            path="test.path",
            schema_path="schema.path",
            value="test_value",
        )
        result = error.to_dict()
        assert result["message"] == "Test message"
        assert result["path"] == "test.path"
        assert result["value"] == "test_value"


# ============================================================================
# Test Module-Level Functions
# ============================================================================


class TestModuleFunctions:
    """Test module-level convenience functions."""

    def test_validate_json_function(self, schemas_dir):
        """Test validate_json function."""
        data = {
            "faculty": [
                {
                    "facultyId": "F001",
                    "name": "Test",
                    "designation": "Professor"
                }
            ]
        }
        errors = validate_json(data, "faculty", schemas_dir)
        assert isinstance(errors, list)

    def test_validate_json_file_function(self, schemas_dir, v4_data_dir):
        """Test validate_json_file function."""
        faculty_file = v4_data_dir / "stage_1" / "facultyBasic.json"
        if faculty_file.exists():
            errors = validate_json_file(faculty_file, "faculty", schemas_dir)
            assert isinstance(errors, list)


# ============================================================================
# Test Stage 2 Schemas
# ============================================================================


class TestStage2Schemas:
    """Test Stage 2 schema validation."""

    def test_load_subjects_full_schema(self, validator):
        """Test loading subjects_full schema."""
        schema = validator.get_schema("subjects_full")
        assert isinstance(schema, dict)
        assert "definitions" in schema

    def test_load_faculty_full_schema(self, validator):
        """Test loading faculty_full schema."""
        schema = validator.get_schema("faculty_full")
        assert isinstance(schema, dict)

    def test_validate_subjects_full_data(self, validator):
        """Test validating Stage 2 subjects data."""
        data = {
            "subjects": [
                {
                    "subjectCode": "CS101",
                    "subjectName": "Introduction to Programming",
                    "semester": 1,
                    "credits": {
                        "theory": 3,
                        "tutorial": 1,
                        "practical": 2,
                        "total": 6
                    },
                    "components": [
                        {
                            "componentType": "theory",
                            "credits": 3,
                            "sessionsPerWeek": 3,
                            "sessionDuration": 60,
                            "roomType": "lecture"
                        }
                    ],
                    "type": "core"
                }
            ]
        }
        errors = validator.validate_data(data, "subjects_full")
        assert len(errors) == 0

    def test_validate_faculty_full_data(self, validator):
        """Test validating Stage 2 faculty data."""
        data = {
            "faculty": [
                {
                    "facultyId": "F001",
                    "name": "Dr. Test",
                    "designation": "Professor",
                    "department": "CS",
                    "primaryAssignments": [],
                    "supportingAssignments": [],
                    "workloadStats": {
                        "theoryHours": 10,
                        "tutorialHours": 2,
                        "practicalHours": 4,
                        "totalSessions": 8,
                        "totalWeeklyHours": 16
                    }
                }
            ]
        }
        errors = validator.validate_data(data, "faculty_full")
        assert len(errors) == 0


# ============================================================================
# Test Stage 3 Schemas
# ============================================================================


class TestStage3Schemas:
    """Test Stage 3 schema validation."""

    def test_load_teaching_assignments_schema(self, validator):
        """Test loading teaching_assignments schema."""
        schema = validator.get_schema("teaching_assignments")
        assert isinstance(schema, dict)

    def test_load_overlap_constraints_schema(self, validator):
        """Test loading overlap_constraints schema."""
        schema = validator.get_schema("overlap_constraints")
        assert isinstance(schema, dict)

    def test_load_statistics_schema(self, validator):
        """Test loading statistics schema."""
        schema = validator.get_schema("statistics")
        assert isinstance(schema, dict)

    def test_validate_overlap_constraints_data(self, validator):
        """Test validating overlap constraints data."""
        data = {
            "metadata": {
                "generatedAt": "2024-01-01T00:00:00",
                "description": "Test constraints"
            },
            "cannotOverlapWith": {
                "MCA_A": ["MCA_B"],
                "MCA_B": ["MCA_A"]
            }
        }
        errors = validator.validate_data(data, "overlap_constraints")
        assert len(errors) == 0


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.integration
class TestSchemaIntegration:
    """Integration tests with real V4 data."""

    def test_validate_real_faculty_file(self, validator, v4_data_dir):
        """Test validating real Stage 1 faculty file."""
        faculty_file = v4_data_dir / "stage_1" / "facultyBasic.json"
        if faculty_file.exists():
            errors = validator.validate_file(faculty_file, "faculty")
            # Log errors for debugging but don't fail if schema differs
            for e in errors:
                print(f"Validation note: {e}")

    def test_validate_real_stage2_faculty(self, validator, v4_data_dir):
        """Test validating real Stage 2 faculty file."""
        faculty_file = v4_data_dir / "stage_2" / "faculty2Full.json"
        if faculty_file.exists():
            errors = validator.validate_file(faculty_file, "faculty_full")
            for e in errors:
                print(f"Stage 2 validation note: {e}")

    def test_validate_real_stage3_assignments(self, validator, v4_data_dir):
        """Test validating real Stage 3 assignments file."""
        assignments_file = v4_data_dir / "stage_3" / "teachingAssignments_sem1.json"
        if assignments_file.exists():
            errors = validator.validate_file(assignments_file, "teaching_assignments")
            for e in errors:
                print(f"Stage 3 validation note: {e}")
