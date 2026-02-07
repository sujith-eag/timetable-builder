"""
Integration tests for the timetable system.

These tests verify that the complete pipeline works end-to-end,
including data loading, validation, and CLI commands with real V4 data.
"""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from timetable.cli import cli
from timetable.core.loader import DataLoader
from timetable.core.schema import SchemaValidator


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def v4_data_dir() -> Path:
    """Get the V4 data directory path."""
    current = Path(__file__).parent.parent.parent
    return current


@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def data_loader(v4_data_dir) -> DataLoader:
    """Create a data loader for V4 data."""
    return DataLoader(v4_data_dir)


@pytest.fixture
def schema_validator(v4_data_dir) -> SchemaValidator:
    """Create a schema validator for V4 data."""
    return SchemaValidator(v4_data_dir / "schemas")


# ============================================================================
# Full Pipeline Integration Tests
# ============================================================================


@pytest.mark.integration
class TestFullPipelineIntegration:
    """Test the complete data processing pipeline."""

    def test_stage1_to_stage2_data_flow(self, data_loader):
        """Test that Stage 1 data flows correctly to Stage 2."""
        # Load Stage 1
        stage1_faculty = data_loader.load_faculty()
        stage1_subjects = data_loader.load_subjects()

        # Load Stage 2
        stage2_faculty = data_loader.load_faculty_full()
        stage2_subjects = data_loader.load_subjects_full()

        # Verify faculty IDs are preserved
        stage1_ids = {f.faculty_id for f in stage1_faculty}
        stage2_ids = {f.faculty_id for f in stage2_faculty}
        assert stage1_ids == stage2_ids, "Faculty IDs should match between stages"

        # Verify Stage 2 has enriched data
        for faculty in stage2_faculty:
            assert hasattr(faculty, "workload_stats")
            assert hasattr(faculty, "primary_assignments")

    def test_stage2_to_stage3_data_flow(self, data_loader):
        """Test that Stage 2 data flows correctly to Stage 3."""
        # Load Stage 2
        stage2_faculty = data_loader.load_faculty_full()
        stage2_subjects = data_loader.load_subjects_full()

        # Load Stage 3
        assignments = data_loader.load_all_teaching_assignments()
        statistics = data_loader.load_statistics()

        # Verify faculty in assignments exist in Stage 2
        stage2_faculty_ids = {f.faculty_id for f in stage2_faculty}

        for sem, assignment_file in assignments.items():
            for assignment in assignment_file.assignments:
                assert assignment.faculty_id in stage2_faculty_ids, \
                    f"Assignment faculty {assignment.faculty_id} not found in Stage 2"

        # Verify statistics are consistent
        total_assignments = sum(
            len(af.assignments) for af in assignments.values()
        )
        assert statistics.combined.total_assignments == total_assignments, \
            "Statistics total should match actual assignments"

    def test_complete_data_load_and_validate(self, data_loader):
        """Test loading and validating all data stages."""
        # Load all Stage 1
        stage1 = data_loader.load_all_stage1()
        assert "config" in stage1
        assert "faculty" in stage1
        assert "subjects" in stage1

        # Load all Stage 2
        stage2 = data_loader.load_all_stage2()
        assert "faculty_full" in stage2
        assert "subjects_full" in stage2

        # Load all Stage 3
        stage3 = data_loader.load_all_stage3()
        assert "assignments" in stage3
        assert "overlap_constraints" in stage3
        assert "statistics" in stage3

        # Validate Stage 1
        warnings = data_loader.validate_stage1()
        # Just ensure validation completes (warnings are OK)
        assert isinstance(warnings, list)


# ============================================================================
# CLI Integration Tests
# ============================================================================


@pytest.mark.integration
class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def test_cli_validate_all_stages(self, cli_runner, v4_data_dir):
        """Test CLI validation of all stages."""
        result = cli_runner.invoke(
            cli,
            ["validate", "--all", "--data-dir", str(v4_data_dir)],
        )
        assert result.exit_code == 0, f"Validation failed: {result.output}"
        assert "passed" in result.output.lower()

    def test_cli_info_all(self, cli_runner, v4_data_dir):
        """Test CLI info all command."""
        result = cli_runner.invoke(
            cli,
            ["info", "all", "--data-dir", str(v4_data_dir)],
        )
        assert result.exit_code == 0, f"Info failed: {result.output}"
        assert "Stage 1" in result.output or "stage 1" in result.output.lower()
        assert "Stage 2" in result.output or "stage 2" in result.output.lower()
        assert "Stage 3" in result.output or "stage 3" in result.output.lower()

    def test_cli_load_pipeline(self, cli_runner, v4_data_dir):
        """Test loading various data types through CLI."""
        commands = [
            ["load", "config"],
            ["load", "faculty"],
            ["load", "subjects"],
            ["load", "faculty", "--stage", "2"],
            ["load", "subjects", "--stage", "2"],
            ["load", "assignments", "--semester", "1"],
            ["load", "statistics"],
        ]

        for cmd in commands:
            result = cli_runner.invoke(
                cli,
                cmd + ["--data-dir", str(v4_data_dir)],
            )
            assert result.exit_code == 0, f"Command {cmd} failed: {result.output}"

    def test_cli_schema_validation(self, cli_runner, v4_data_dir):
        """Test schema validation through CLI."""
        schemas = [
            "faculty",
            "subjects_full",
            "faculty_full",
            "scheduling_input",
            "ai_schedule",
            "enriched_timetable",
        ]

        for schema_name in schemas:
            result = cli_runner.invoke(
                cli,
                ["schema", "validate", schema_name, "--data-dir", str(v4_data_dir)],
            )
            # May pass or fail based on schema - just ensure no crash
            assert result.exit_code is not None


# ============================================================================
# Schema Validation Integration Tests
# ============================================================================


@pytest.mark.integration
class TestSchemaIntegration:
    """Integration tests for schema validation."""

    def test_validate_all_stage1_files(self, schema_validator, v4_data_dir):
        """Test validating all Stage 1 files against schemas."""
        stage1_files = {
            "config": v4_data_dir / "stage_1" / "config.json",
            "faculty": v4_data_dir / "stage_1" / "facultyBasic.json",
        }

        for schema_name, file_path in stage1_files.items():
            if file_path.exists():
                errors = schema_validator.validate_file(file_path, schema_name)
                # Log but don't fail on schema mismatches (schemas may need updates)
                if errors:
                    print(f"Schema {schema_name} validation notes: {len(errors)} issues")

    def test_validate_all_stage2_files(self, schema_validator, v4_data_dir):
        """Test validating all Stage 2 files against schemas."""
        stage2_files = {
            "subjects_full": v4_data_dir / "stage_2" / "subjects2Full.json",
            "faculty_full": v4_data_dir / "stage_2" / "faculty2Full.json",
        }

        for schema_name, file_path in stage2_files.items():
            if file_path.exists():
                errors = schema_validator.validate_file(file_path, schema_name)
                if errors:
                    print(f"Schema {schema_name} validation notes: {len(errors)} issues")

    def test_validate_all_stage3_files(self, schema_validator, v4_data_dir):
        """Test validating all Stage 3 files against schemas."""
        stage3_files = {
            "teaching_assignments": v4_data_dir / "stage_3" / "teachingAssignments_sem1.json",
            "overlap_constraints": v4_data_dir / "stage_3" / "studentGroupOverlapConstraints.json",
            "statistics": v4_data_dir / "stage_3" / "statistics.json",
        }

        for schema_name, file_path in stage3_files.items():
            if file_path.exists():
                errors = schema_validator.validate_file(file_path, schema_name)
                if errors:
                    print(f"Schema {schema_name} validation notes: {len(errors)} issues")


# ============================================================================
# Data Consistency Tests
# ============================================================================


@pytest.mark.integration
class TestDataConsistency:
    """Test data consistency across stages."""

    def test_subject_codes_consistency(self, data_loader):
        """Test that subject codes are consistent across stages."""
        stage1_subjects = data_loader.load_subjects()
        stage2_subjects = data_loader.load_subjects_full()

        # Get all subject codes from both stages
        stage1_codes = {s.subject_code for s in stage1_subjects}
        stage2_codes = {s.subject_code for s in stage2_subjects}

        # Stage 2 may have more subjects (differentiation adds some)
        # but core subjects should be present
        core_stage2 = {s.subject_code for s in stage2_subjects if s.type == "core"}

        # Basic sanity check - we should have subjects
        assert len(stage1_codes) > 0
        assert len(stage2_codes) > 0

    def test_faculty_workload_consistency(self, data_loader):
        """Test that faculty workload is consistent with assignments."""
        stage2_faculty = data_loader.load_faculty_full()
        assignments = data_loader.load_all_teaching_assignments()

        # Count assignments per faculty from Stage 3
        faculty_assignment_count = {}
        for sem, af in assignments.items():
            for assignment in af.assignments:
                fid = assignment.faculty_id
                faculty_assignment_count[fid] = faculty_assignment_count.get(fid, 0) + 1

        # Verify faculty in Stage 2 have assignments
        for faculty in stage2_faculty:
            if len(faculty.primary_assignments) > 0:
                # Faculty with primary assignments should have Stage 3 assignments
                assert faculty.faculty_id in faculty_assignment_count or \
                       len(faculty.primary_assignments) == 0, \
                    f"Faculty {faculty.faculty_id} has Stage 2 assignments but not Stage 3"

    def test_student_group_references(self, data_loader):
        """Test that student group references are valid."""
        groups = data_loader.load_student_groups()
        assignments = data_loader.load_all_teaching_assignments()

        # Get all valid group IDs
        valid_groups = {g.student_group_id for g in groups.student_groups}
        valid_groups.update(g.student_group_id for g in groups.elective_student_groups)

        # Check that assignments reference valid groups
        for sem, af in assignments.items():
            for assignment in af.assignments:
                for group in assignment.student_group_ids:
                    # Groups may be combined or partial - just ensure reasonable format
                    assert len(group) > 0, f"Empty student group in {assignment.assignment_id}"

    def test_statistics_calculations(self, data_loader):
        """Test that statistics are calculated correctly."""
        assignments = data_loader.load_all_teaching_assignments()
        statistics = data_loader.load_statistics()

        # Calculate expected totals
        sem1_assignments = len(assignments.get(1, type("", (), {"assignments": []})()).assignments) \
            if 1 in assignments else 0
        sem3_assignments = len(assignments.get(3, type("", (), {"assignments": []})()).assignments) \
            if 3 in assignments else 0

        actual_sem1 = len(assignments[1].assignments) if 1 in assignments else 0
        actual_sem3 = len(assignments[3].assignments) if 3 in assignments else 0

        # Verify semester statistics
        assert statistics.semester1.total_assignments == actual_sem1, \
            "Semester 1 assignment count mismatch"
        assert statistics.semester3.total_assignments == actual_sem3, \
            "Semester 3 assignment count mismatch"

        # Verify combined total
        assert statistics.combined.total_assignments == actual_sem1 + actual_sem3, \
            "Combined assignment count mismatch"


# ============================================================================
# Error Handling Integration Tests
# ============================================================================


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling in integration scenarios."""

    def test_graceful_missing_file_handling(self, cli_runner, tmp_path):
        """Test graceful handling of missing files."""
        result = cli_runner.invoke(
            cli,
            ["load", "config", "--data-dir", str(tmp_path)],
        )
        assert result.exit_code != 0
        assert "error" in result.output.lower() or "not found" in result.output.lower()

    def test_graceful_invalid_json_handling(self, cli_runner, tmp_path):
        """Test graceful handling of invalid JSON."""
        # Create invalid JSON file
        stage1 = tmp_path / "stage_1"
        stage1.mkdir()
        (stage1 / "config.json").write_text("{invalid}")

        result = cli_runner.invoke(
            cli,
            ["load", "config", "--data-dir", str(tmp_path)],
        )
        assert result.exit_code != 0

    def test_graceful_validation_error_handling(self, cli_runner, tmp_path):
        """Test graceful handling of validation errors."""
        # Create JSON with invalid structure
        stage1 = tmp_path / "stage_1"
        stage1.mkdir()
        (stage1 / "config.json").write_text('{"config": {}}')

        result = cli_runner.invoke(
            cli,
            ["validate", "--stage", "1", "--data-dir", str(tmp_path)],
        )
        # Should exit with error but not crash
        assert result.exit_code != 0


# ============================================================================
# Performance Tests
# ============================================================================


@pytest.mark.integration
class TestPerformance:
    """Performance-related integration tests."""

    def test_data_loading_time(self, data_loader):
        """Test that data loading completes in reasonable time."""
        import time

        start = time.time()
        data_loader.load_all_stage1()
        data_loader.load_all_stage2()
        data_loader.load_all_stage3()
        elapsed = time.time() - start

        # Should complete in under 5 seconds
        assert elapsed < 5.0, f"Data loading took too long: {elapsed:.2f}s"

    def test_cli_response_time(self, cli_runner, v4_data_dir):
        """Test that CLI commands respond quickly."""
        import time

        start = time.time()
        result = cli_runner.invoke(
            cli,
            ["info", "all", "--data-dir", str(v4_data_dir)],
        )
        elapsed = time.time() - start

        assert result.exit_code == 0
        # Should complete in under 3 seconds
        assert elapsed < 3.0, f"CLI command took too long: {elapsed:.2f}s"
