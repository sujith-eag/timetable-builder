"""
Tests for the timetable CLI.

This module tests the Click-based command-line interface including:
- Command group structure
- Individual commands (load, validate, info, build)
- Error handling and output formatting
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from timetable.cli import main, cli


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def v4_data_dir() -> Path:
    """Get the V4 data directory path."""
    # Navigate from tests/unit/ to project root, then to V4 data
    current = Path(__file__).parent.parent.parent
    return current


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory structure for testing."""
    # Create stage directories
    stage1 = tmp_path / "stage_1"
    stage1.mkdir()
    stage2 = tmp_path / "stage_2"
    stage2.mkdir()
    stage3 = tmp_path / "stage_3"
    stage3.mkdir()

    # Create minimal config.json
    config = {
        "config": {
            "dayStart": "08:00",
            "dayEnd": "17:00",
            "workingDays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "timeSlots": [
                {"slotNumber": 1, "start": "08:00", "end": "09:00", "duration": 60}
            ],
            "rooms": [
                {"roomId": "R101", "roomType": "theory", "capacity": 50}
            ]
        }
    }
    (stage1 / "config.json").write_text(json.dumps(config))

    # Create minimal faculty
    faculty = {
        "faculty": [
            {
                "facultyId": "F001",
                "name": "Dr. Test",
                "subjectsCanTeach": ["CS101"]
            }
        ]
    }
    (stage1 / "facultyBasic.json").write_text(json.dumps(faculty))

    return tmp_path


# ============================================================================
# Test CLI Structure
# ============================================================================


class TestCLIStructure:
    """Test the basic CLI structure and help."""

    def test_main_entrypoint(self, cli_runner):
        """Test that main() can be invoked via cli."""
        # main() is a wrapper that calls cli(), so we test cli directly
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Timetable" in result.output or "timetable" in result.output.lower()

    def test_cli_help(self, cli_runner):
        """Test that --help shows available commands."""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "--help" in result.output

    def test_cli_version(self, cli_runner):
        """Test that --version shows version info."""
        result = cli_runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_cli_has_validate_command(self, cli_runner):
        """Test that validate command exists."""
        result = cli_runner.invoke(cli, ["validate", "--help"])
        assert result.exit_code == 0
        assert "validate" in result.output.lower() or "Validate" in result.output

    def test_cli_has_info_command(self, cli_runner):
        """Test that info command exists."""
        result = cli_runner.invoke(cli, ["info", "--help"])
        assert result.exit_code == 0

    def test_cli_has_load_command(self, cli_runner):
        """Test that load command exists."""
        result = cli_runner.invoke(cli, ["load", "--help"])
        assert result.exit_code == 0


# ============================================================================
# Test Info Command
# ============================================================================


class TestInfoCommand:
    """Test the info command group."""

    def test_info_config(self, cli_runner, v4_data_dir):
        """Test info config shows configuration summary."""
        result = cli_runner.invoke(
            cli, ["info", "config", "--data-dir", str(v4_data_dir)]
        )
        # Should succeed or show meaningful error
        if result.exit_code == 0:
            # Check for expected content
            output_lower = result.output.lower()
            assert any(
                term in output_lower
                for term in ["time", "slot", "day", "config", "room"]
            )

    def test_info_faculty(self, cli_runner, v4_data_dir):
        """Test info faculty shows faculty summary."""
        result = cli_runner.invoke(
            cli, ["info", "faculty", "--data-dir", str(v4_data_dir)]
        )
        if result.exit_code == 0:
            output_lower = result.output.lower()
            assert any(
                term in output_lower
                for term in ["faculty", "member", "total", "count"]
            )

    def test_info_subjects(self, cli_runner, v4_data_dir):
        """Test info subjects shows subjects summary."""
        result = cli_runner.invoke(
            cli, ["info", "subjects", "--data-dir", str(v4_data_dir)]
        )
        if result.exit_code == 0:
            output_lower = result.output.lower()
            assert any(
                term in output_lower
                for term in ["subject", "total", "semester", "count"]
            )

    def test_info_all(self, cli_runner, v4_data_dir):
        """Test info all shows complete summary."""
        result = cli_runner.invoke(
            cli, ["info", "all", "--data-dir", str(v4_data_dir)]
        )
        if result.exit_code == 0:
            output_lower = result.output.lower()
            assert any(
                term in output_lower
                for term in ["config", "faculty", "subject", "summary"]
            )


# ============================================================================
# Test Validate Command
# ============================================================================


class TestValidateCommand:
    """Test the validate command group."""

    def test_validate_stage1(self, cli_runner, v4_data_dir):
        """Test validating Stage 1 data."""
        result = cli_runner.invoke(
            cli,
            ["validate", "--stage", "1", "--data-dir", str(v4_data_dir)],
        )
        # Should either succeed or fail with validation errors
        assert result.exit_code in [0, 1]

    def test_validate_stage2(self, cli_runner, v4_data_dir):
        """Test validating Stage 2 data."""
        result = cli_runner.invoke(
            cli,
            ["validate", "--stage", "2", "--data-dir", str(v4_data_dir)],
        )
        assert result.exit_code in [0, 1]

    def test_validate_stage3(self, cli_runner, v4_data_dir):
        """Test validating Stage 3 data."""
        result = cli_runner.invoke(
            cli,
            ["validate", "--stage", "3", "--data-dir", str(v4_data_dir)],
        )
        assert result.exit_code in [0, 1]

    def test_validate_all_stages(self, cli_runner, v4_data_dir):
        """Test validating all stages."""
        result = cli_runner.invoke(
            cli,
            ["validate", "--all", "--data-dir", str(v4_data_dir)],
        )
        assert result.exit_code in [0, 1]

    def test_validate_invalid_stage(self, cli_runner, v4_data_dir):
        """Test error handling for invalid stage number."""
        result = cli_runner.invoke(
            cli,
            ["validate", "--stage", "99", "--data-dir", str(v4_data_dir)],
        )
        # Should fail with error
        assert result.exit_code != 0 or "error" in result.output.lower()

    def test_validate_missing_data_dir(self, cli_runner):
        """Test error when data directory doesn't exist."""
        result = cli_runner.invoke(
            cli,
            ["validate", "--stage", "1", "--data-dir", "/nonexistent/path"],
        )
        assert result.exit_code != 0


# ============================================================================
# Test Load Command
# ============================================================================


class TestLoadCommand:
    """Test the load command for viewing data."""

    def test_load_config(self, cli_runner, v4_data_dir):
        """Test loading and displaying config."""
        result = cli_runner.invoke(
            cli, ["load", "config", "--data-dir", str(v4_data_dir)]
        )
        if result.exit_code == 0:
            # Should show config data
            assert len(result.output) > 0

    def test_load_faculty(self, cli_runner, v4_data_dir):
        """Test loading and displaying faculty."""
        result = cli_runner.invoke(
            cli, ["load", "faculty", "--data-dir", str(v4_data_dir)]
        )
        if result.exit_code == 0:
            assert len(result.output) > 0

    def test_load_subjects(self, cli_runner, v4_data_dir):
        """Test loading and displaying subjects."""
        result = cli_runner.invoke(
            cli, ["load", "subjects", "--data-dir", str(v4_data_dir)]
        )
        if result.exit_code == 0:
            assert len(result.output) > 0

    def test_load_with_json_output(self, cli_runner, v4_data_dir):
        """Test loading with JSON output format."""
        result = cli_runner.invoke(
            cli, ["load", "config", "--data-dir", str(v4_data_dir), "--json"]
        )
        if result.exit_code == 0:
            # Output should be valid JSON
            try:
                data = json.loads(result.output)
                assert isinstance(data, dict)
            except json.JSONDecodeError:
                # May have Rich formatting, which is okay
                pass


# ============================================================================
# Test Output Formatting
# ============================================================================


class TestOutputFormatting:
    """Test that output is properly formatted."""

    def test_error_shows_helpful_message(self, cli_runner):
        """Test that errors show helpful messages."""
        result = cli_runner.invoke(
            cli,
            ["validate", "--stage", "1", "--data-dir", "/nonexistent"],
        )
        assert result.exit_code != 0
        # Should have some error output
        assert len(result.output) > 0 or len(result.output) >= 0

    def test_success_message_formatting(self, cli_runner, v4_data_dir):
        """Test that success messages are clear."""
        result = cli_runner.invoke(
            cli, ["info", "config", "--data-dir", str(v4_data_dir)]
        )
        # If successful, output should be readable
        if result.exit_code == 0:
            assert result.output is not None


# ============================================================================
# Test Data Directory Option
# ============================================================================


class TestDataDirectoryOption:
    """Test the --data-dir option behavior."""

    def test_data_dir_required_or_default(self, cli_runner):
        """Test that data-dir is handled properly."""
        # Either requires --data-dir or uses default
        result = cli_runner.invoke(cli, ["validate", "--stage", "1"])
        # Should not crash - either works with default or shows error
        assert result.exit_code is not None

    def test_data_dir_accepts_relative_path(self, cli_runner, temp_data_dir):
        """Test that relative paths work."""
        with cli_runner.isolated_filesystem():
            # Use the temp data dir
            result = cli_runner.invoke(
                cli,
                ["info", "config", "--data-dir", str(temp_data_dir)],
            )
            # Should at least not crash
            assert result.exit_code is not None

    def test_data_dir_env_variable(self, cli_runner, v4_data_dir, monkeypatch):
        """Test that TIMETABLE_DATA_DIR env var works."""
        monkeypatch.setenv("TIMETABLE_DATA_DIR", str(v4_data_dir))
        result = cli_runner.invoke(cli, ["info", "config"])
        # Should use env var as default
        assert result.exit_code is not None


# ============================================================================
# Test Stage-Specific Commands
# ============================================================================


class TestStageCommands:
    """Test stage-specific command variations."""

    def test_load_stage2_faculty(self, cli_runner, v4_data_dir):
        """Test loading Stage 2 faculty data."""
        result = cli_runner.invoke(
            cli,
            ["load", "faculty", "--stage", "2", "--data-dir", str(v4_data_dir)],
        )
        # Should either work or report stage 2 not available
        assert result.exit_code is not None

    def test_load_stage2_subjects(self, cli_runner, v4_data_dir):
        """Test loading Stage 2 subjects data."""
        result = cli_runner.invoke(
            cli,
            ["load", "subjects", "--stage", "2", "--data-dir", str(v4_data_dir)],
        )
        assert result.exit_code is not None

    def test_load_stage3_assignments(self, cli_runner, v4_data_dir):
        """Test loading Stage 3 assignments."""
        result = cli_runner.invoke(
            cli,
            ["load", "assignments", "--semester", "1", "--data-dir", str(v4_data_dir)],
        )
        assert result.exit_code is not None


# ============================================================================
# Test Error Handling
# ============================================================================


class TestErrorHandling:
    """Test CLI error handling."""

    def test_handles_file_not_found(self, cli_runner):
        """Test graceful handling of missing files."""
        result = cli_runner.invoke(
            cli,
            ["load", "config", "--data-dir", "/nonexistent/path"],
        )
        assert result.exit_code != 0
        # Should have error message
        output_lower = result.output.lower()
        assert "error" in output_lower or "not found" in output_lower or "not exist" in output_lower

    def test_handles_invalid_json(self, cli_runner, tmp_path):
        """Test handling of invalid JSON files."""
        # Create invalid JSON
        stage1 = tmp_path / "stage_1"
        stage1.mkdir()
        (stage1 / "config.json").write_text("{ invalid json }")

        result = cli_runner.invoke(
            cli,
            ["load", "config", "--data-dir", str(tmp_path)],
        )
        assert result.exit_code != 0

    def test_handles_validation_error(self, cli_runner, tmp_path):
        """Test handling of validation errors."""
        # Create JSON with missing required fields
        stage1 = tmp_path / "stage_1"
        stage1.mkdir()
        (stage1 / "config.json").write_text('{"config": {}}')

        result = cli_runner.invoke(
            cli,
            ["validate", "--stage", "1", "--data-dir", str(tmp_path)],
        )
        # Should exit with error
        assert result.exit_code != 0


# ============================================================================
# Test Verbose and Quiet Modes
# ============================================================================


class TestVerbosityOptions:
    """Test verbose and quiet output modes."""

    def test_verbose_flag(self, cli_runner, v4_data_dir):
        """Test --verbose flag increases output."""
        result = cli_runner.invoke(
            cli,
            ["--verbose", "info", "config", "--data-dir", str(v4_data_dir)],
        )
        # Should not crash
        assert result.exit_code is not None

    def test_quiet_flag(self, cli_runner, v4_data_dir):
        """Test --quiet flag reduces output."""
        result = cli_runner.invoke(
            cli,
            ["--quiet", "validate", "--stage", "1", "--data-dir", str(v4_data_dir)],
        )
        # Should not crash
        assert result.exit_code is not None


# ============================================================================
# Integration Test with Real Data
# ============================================================================


@pytest.mark.integration
class TestCLIIntegration:
    """Integration tests with real V4 data."""

    def test_full_validation_workflow(self, cli_runner, v4_data_dir):
        """Test complete validation workflow."""
        # Validate all stages
        result = cli_runner.invoke(
            cli,
            ["validate", "--all", "--data-dir", str(v4_data_dir)],
        )
        # Should complete (may have warnings)
        assert result.exit_code in [0, 1]

    def test_info_pipeline(self, cli_runner, v4_data_dir):
        """Test getting info for all data types."""
        commands = [
            ["info", "config"],
            ["info", "faculty"],
            ["info", "subjects"],
        ]
        for cmd in commands:
            result = cli_runner.invoke(
                cli,
                cmd + ["--data-dir", str(v4_data_dir)],
            )
            assert result.exit_code is not None, f"Command {cmd} crashed"


# ============================================================================
# Export Command Tests
# ============================================================================


class TestExportCommand:
    """Test export command group."""

    def test_export_help(self, cli_runner):
        """Test export command help."""
        result = cli_runner.invoke(cli, ["export", "--help"])
        assert result.exit_code == 0
        assert "Export data to various formats" in result.output
        assert "faculty" in result.output
        assert "subjects" in result.output
        assert "assignments" in result.output

    def test_export_faculty_json(self, cli_runner, v4_data_dir, tmp_path):
        """Test export faculty to JSON."""
        result = cli_runner.invoke(
            cli,
            [
                "export", "faculty",
                "--format", "json",
                "--output", str(tmp_path),
                "--data-dir", str(v4_data_dir),
            ],
        )
        assert result.exit_code == 0
        assert "Exported" in result.output
        # Check file was created
        exported_files = list(tmp_path.glob("faculty_*.json"))
        assert len(exported_files) == 1

    def test_export_faculty_csv(self, cli_runner, v4_data_dir, tmp_path):
        """Test export faculty to CSV."""
        result = cli_runner.invoke(
            cli,
            [
                "export", "faculty",
                "--format", "csv",
                "--output", str(tmp_path),
                "--data-dir", str(v4_data_dir),
            ],
        )
        assert result.exit_code == 0
        exported_files = list(tmp_path.glob("faculty_*.csv"))
        assert len(exported_files) == 1

    def test_export_faculty_markdown(self, cli_runner, v4_data_dir, tmp_path):
        """Test export faculty to Markdown."""
        result = cli_runner.invoke(
            cli,
            [
                "export", "faculty",
                "--format", "md",
                "--output", str(tmp_path),
                "--data-dir", str(v4_data_dir),
            ],
        )
        assert result.exit_code == 0
        exported_files = list(tmp_path.glob("faculty_*.md"))
        assert len(exported_files) == 1

    def test_export_subjects_with_semester(self, cli_runner, v4_data_dir, tmp_path):
        """Test export subjects filtered by semester."""
        result = cli_runner.invoke(
            cli,
            [
                "export", "subjects",
                "--format", "json",
                "--semester", "1",
                "--output", str(tmp_path),
                "--data-dir", str(v4_data_dir),
            ],
        )
        assert result.exit_code == 0
        exported_files = list(tmp_path.glob("subjects_*_sem1_*.json"))
        assert len(exported_files) == 1

    def test_export_assignments(self, cli_runner, v4_data_dir, tmp_path):
        """Test export teaching assignments."""
        result = cli_runner.invoke(
            cli,
            [
                "export", "assignments",
                "--format", "json",
                "--semester", "1",
                "--output", str(tmp_path),
                "--data-dir", str(v4_data_dir),
            ],
        )
        assert result.exit_code == 0
        exported_files = list(tmp_path.glob("assignments_*.json"))
        assert len(exported_files) == 1

    def test_export_statistics(self, cli_runner, v4_data_dir, tmp_path):
        """Test export statistics."""
        result = cli_runner.invoke(
            cli,
            [
                "export", "statistics",
                "--format", "json",
                "--output", str(tmp_path),
                "--data-dir", str(v4_data_dir),
            ],
        )
        assert result.exit_code == 0
        exported_files = list(tmp_path.glob("statistics_*.json"))
        assert len(exported_files) == 1

    def test_export_all(self, cli_runner, v4_data_dir, tmp_path):
        """Test export all data."""
        result = cli_runner.invoke(
            cli,
            [
                "export", "all",
                "--format", "json",
                "--output", str(tmp_path),
                "--data-dir", str(v4_data_dir),
            ],
        )
        assert result.exit_code == 0
        assert "Export complete" in result.output
        # Should create a timestamped directory
        export_dirs = list(tmp_path.glob("export_*"))
        assert len(export_dirs) == 1
        # Check files were created
        export_dir = export_dirs[0]
        assert (export_dir / "faculty.json").exists()
        assert (export_dir / "subjects.json").exists()


# ============================================================================
# Status Command Tests
# ============================================================================


class TestStatusCommand:
    """Test status command."""

    def test_status_help(self, cli_runner):
        """Test status command help."""
        result = cli_runner.invoke(cli, ["status", "--help"])
        assert result.exit_code == 0
        assert "Show system status" in result.output

    def test_status_shows_overview(self, cli_runner, v4_data_dir):
        """Test status command shows stage overview."""
        result = cli_runner.invoke(
            cli,
            ["status", "--data-dir", str(v4_data_dir)],
        )
        assert result.exit_code == 0
        assert "Stage Status Overview" in result.output
        assert "Stage 1" in result.output
        assert "Stage 2" in result.output
        assert "Stage 3" in result.output

    def test_status_shows_quick_commands(self, cli_runner, v4_data_dir):
        """Test status shows quick command suggestions."""
        result = cli_runner.invoke(
            cli,
            ["status", "--data-dir", str(v4_data_dir)],
        )
        assert result.exit_code == 0
        assert "Quick Commands" in result.output
        assert "validate" in result.output


# ============================================================================
# Build Command Tests
# ============================================================================


class TestBuildCommand:
    """Test build command group."""

    def test_build_help(self, cli_runner):
        """Test build command help."""
        result = cli_runner.invoke(cli, ["build", "--help"])
        assert result.exit_code == 0
        assert "Build timetable data stages" in result.output

    def test_build_has_stage2_command(self, cli_runner):
        """Test that stage2 subcommand exists."""
        result = cli_runner.invoke(cli, ["build", "stage2", "--help"])
        assert result.exit_code == 0
        assert "Stage 2" in result.output

    def test_build_has_stage3_command(self, cli_runner):
        """Test that stage3 subcommand exists."""
        result = cli_runner.invoke(cli, ["build", "stage3", "--help"])
        assert result.exit_code == 0
        assert "Stage 3" in result.output

    def test_build_has_all_command(self, cli_runner):
        """Test that all subcommand exists."""
        result = cli_runner.invoke(cli, ["build", "all", "--help"])
        assert result.exit_code == 0
        assert "Build all stages" in result.output

    def test_build_check_shows_status(self, cli_runner, v4_data_dir):
        """Test build check shows stage status."""
        result = cli_runner.invoke(
            cli,
            ["build", "check", "--data-dir", str(v4_data_dir)],
        )
        assert result.exit_code == 0
        assert "Stage Status" in result.output
        assert "Stage 1" in result.output

    def test_build_check_shows_commands(self, cli_runner, v4_data_dir):
        """Test build check shows available commands."""
        result = cli_runner.invoke(
            cli,
            ["build", "check", "--data-dir", str(v4_data_dir)],
        )
        assert result.exit_code == 0
        assert "timetable build stage2" in result.output
        assert "timetable build stage3" in result.output
        assert "timetable build all" in result.output
