"""
Unit tests for the data loader module.

Tests cover file loading, validation, and error handling.
"""

import json
from pathlib import Path

import pytest


class TestLoadJson:
    """Tests for load_json function."""

    def test_load_valid_json(self, temp_dir: Path):
        """load_json should parse valid JSON files."""
        from timetable.core.loader import load_json

        data = {"key": "value", "number": 42}
        filepath = temp_dir / "test.json"
        filepath.write_text(json.dumps(data))

        result = load_json(filepath)
        assert result == data

    def test_load_nonexistent_file(self, temp_dir: Path):
        """load_json should raise DataLoadError for missing files."""
        from timetable.core.exceptions import DataLoadError
        from timetable.core.loader import load_json

        with pytest.raises(DataLoadError) as exc_info:
            load_json(temp_dir / "nonexistent.json")
        assert "not found" in str(exc_info.value).lower()
        assert exc_info.value.filepath is not None

    def test_load_invalid_json(self, temp_dir: Path):
        """load_json should raise DataLoadError for invalid JSON."""
        from timetable.core.exceptions import DataLoadError
        from timetable.core.loader import load_json

        filepath = temp_dir / "invalid.json"
        filepath.write_text("{ invalid json }")

        with pytest.raises(DataLoadError) as exc_info:
            load_json(filepath)
        assert "json" in str(exc_info.value).lower()

    def test_load_directory_path(self, temp_dir: Path):
        """load_json should raise DataLoadError for directory paths."""
        from timetable.core.exceptions import DataLoadError
        from timetable.core.loader import load_json

        with pytest.raises(DataLoadError) as exc_info:
            load_json(temp_dir)
        assert "not a file" in str(exc_info.value).lower()

    def test_load_json_with_string_path(self, temp_dir: Path):
        """load_json should accept string paths."""
        from timetable.core.loader import load_json

        data = {"test": True}
        filepath = temp_dir / "test.json"
        filepath.write_text(json.dumps(data))

        result = load_json(str(filepath))
        assert result == data


class TestValidateModel:
    """Tests for validate_model function."""

    def test_validate_valid_data(self):
        """validate_model should accept valid data."""
        from timetable.core.loader import validate_model
        from timetable.models.stage1 import Subject

        data = {
            "subjectCode": "CS101",
            "shortCode": "CS",
            "title": "Test Subject",
            "creditPattern": [3, 0, 1],
            "totalCredits": 4,
            "department": "MCA",
            "semester": 1,
            "isElective": False,
            "type": "core",
        }
        subject = validate_model(data, Subject)
        assert subject.subject_code == "CS101"

    def test_validate_invalid_data(self):
        """validate_model should raise ValidationError for invalid data."""
        from timetable.core.exceptions import ValidationError
        from timetable.core.loader import validate_model
        from timetable.models.stage1 import Subject

        data = {
            "subjectCode": "CS101",
            # Missing required fields
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_model(data, Subject)
        assert "validation failed" in str(exc_info.value).lower()

    def test_validate_with_filepath_context(self):
        """validate_model should include filepath in error."""
        from timetable.core.exceptions import ValidationError
        from timetable.core.loader import validate_model
        from timetable.models.stage1 import Subject

        with pytest.raises(ValidationError) as exc_info:
            validate_model({}, Subject, filepath="/test/file.json")
        assert exc_info.value.details.get("filepath") == "/test/file.json"


class TestLoadAndValidate:
    """Tests for load_and_validate function."""

    def test_load_and_validate_success(self, temp_dir: Path):
        """load_and_validate should load and validate JSON files."""
        from timetable.core.loader import load_and_validate
        from timetable.models.stage1 import SubjectFile

        data = {
            "subjects": [
                {
                    "subjectCode": "CS101",
                    "shortCode": "CS",
                    "title": "Test",
                    "creditPattern": [3, 0, 1],
                    "totalCredits": 4,
                    "department": "MCA",
                    "semester": 1,
                    "isElective": False,
                    "type": "core",
                }
            ]
        }
        filepath = temp_dir / "subjects.json"
        filepath.write_text(json.dumps(data))

        result = load_and_validate(filepath, SubjectFile)
        assert len(result.subjects) == 1
        assert result.subjects[0].subject_code == "CS101"

    def test_load_and_validate_file_error(self, temp_dir: Path):
        """load_and_validate should propagate file errors."""
        from timetable.core.exceptions import DataLoadError
        from timetable.core.loader import load_and_validate
        from timetable.models.stage1 import SubjectFile

        with pytest.raises(DataLoadError):
            load_and_validate(temp_dir / "missing.json", SubjectFile)

    def test_load_and_validate_validation_error(self, temp_dir: Path):
        """load_and_validate should propagate validation errors."""
        from timetable.core.exceptions import ValidationError
        from timetable.core.loader import load_and_validate
        from timetable.models.stage1 import SubjectFile

        # Invalid data (missing required fields)
        filepath = temp_dir / "invalid.json"
        filepath.write_text('{"subjects": [{}]}')

        with pytest.raises(ValidationError):
            load_and_validate(filepath, SubjectFile)


class TestDataLoader:
    """Tests for DataLoader class."""

    @pytest.fixture
    def loader(self, stage1_data_dir: Path) -> "DataLoader":
        """Create a DataLoader with test data."""
        from timetable.core.loader import DataLoader

        return DataLoader(stage1_data_dir.parent)

    def test_init_with_valid_dir(self, temp_data_dir: Path):
        """DataLoader should initialize with valid directory."""
        from timetable.core.loader import DataLoader

        loader = DataLoader(temp_data_dir)
        assert loader.data_dir == temp_data_dir

    def test_init_with_invalid_dir(self, temp_dir: Path):
        """DataLoader should raise error for invalid directory."""
        from timetable.core.exceptions import DataLoadError
        from timetable.core.loader import DataLoader

        with pytest.raises(DataLoadError):
            DataLoader(temp_dir / "nonexistent")

    def test_stage_dir(self, temp_data_dir: Path):
        """DataLoader should return correct stage directories."""
        from timetable.core.loader import DataLoader

        loader = DataLoader(temp_data_dir)
        assert loader.stage_dir(1) == temp_data_dir / "stage_1"
        assert loader.stage_dir(3) == temp_data_dir / "stage_3"

    def test_load_config(self, loader, stage1_data_dir: Path):
        """DataLoader should load config.json."""
        config = loader.load_config()
        assert config is not None
        assert len(config.time_slots) > 0

    def test_load_faculty(self, loader, stage1_data_dir: Path):
        """DataLoader should load facultyBasic.json."""
        faculty = loader.load_faculty()
        assert len(faculty) > 0
        assert all(f.faculty_id for f in faculty)

    def test_load_subjects(self, loader, stage1_data_dir: Path):
        """DataLoader should load subject files."""
        subjects = loader.load_subjects()
        assert len(subjects) > 0

    def test_load_subjects_by_semester(self, loader, stage1_data_dir: Path):
        """DataLoader should filter subjects by semester."""
        # Need to add sem 1 subjects to fixtures
        subjects = loader.load_subjects(semester=1)
        assert all(s.semester == 1 for s in subjects)

    def test_load_student_groups(self, loader, stage1_data_dir: Path):
        """DataLoader should load studentGroups.json."""
        groups = loader.load_student_groups()
        assert len(groups.student_groups) > 0

    def test_cache_clearing(self, loader):
        """DataLoader should support cache clearing."""
        config1 = loader.load_config()
        loader.clear_cache()
        config2 = loader.load_config()
        # Both should work, cache doesn't affect correctness
        assert config1 is not None
        assert config2 is not None


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_load_config_function(self, stage1_data_dir: Path):
        """load_config should load config files."""
        from timetable.core.loader import load_config

        config = load_config(stage1_data_dir / "config.json")
        assert config is not None

    def test_load_faculty_function(self, stage1_data_dir: Path):
        """load_faculty should load faculty files."""
        from timetable.core.loader import load_faculty

        faculty = load_faculty(stage1_data_dir / "facultyBasic.json")
        assert len(faculty) > 0

    def test_load_subjects_function(self, temp_dir: Path):
        """load_subjects should load subject files."""
        from timetable.core.loader import load_subjects

        data = {
            "subjects": [
                {
                    "subjectCode": "CS101",
                    "shortCode": "CS",
                    "title": "Test",
                    "creditPattern": [3, 0, 1],
                    "totalCredits": 4,
                    "department": "MCA",
                    "semester": 1,
                    "isElective": False,
                    "type": "core",
                }
            ]
        }
        filepath = temp_dir / "subjects.json"
        filepath.write_text(json.dumps(data))

        subjects = load_subjects(filepath)
        assert len(subjects) == 1


class TestDataLoaderWithRealData:
    """Integration tests with actual stage_1 data."""

    @pytest.fixture
    def real_loader(self) -> "DataLoader":
        """Create loader with real V4 data if available."""
        from timetable.core.loader import DataLoader

        # Try to find real data (3 levels up from tests/unit/test_loader.py)
        v4_path = Path(__file__).parent.parent.parent / "stage_1"
        if v4_path.exists():
            return DataLoader(v4_path.parent)
        pytest.skip("Real V4 data not available")

    def test_load_real_config(self, real_loader):
        """Load real config.json."""
        config = real_loader.load_config()
        assert len(config.time_slots) == 7
        assert len(config.weekdays) == 6

    def test_load_real_faculty(self, real_loader):
        """Load real facultyBasic.json."""
        faculty = real_loader.load_faculty()
        assert len(faculty) >= 10  # We know there are 12 faculty

    def test_load_real_subjects(self, real_loader):
        """Load all real subjects."""
        subjects = real_loader.load_subjects()
        assert len(subjects) >= 10  # Multiple subjects across semesters

    def test_load_real_student_groups(self, real_loader):
        """Load real studentGroups.json."""
        groups = real_loader.load_student_groups()
        assert len(groups.student_groups) >= 4  # 4 main groups

    def test_load_real_room_preferences(self, real_loader):
        """Load real roomPreferences.json."""
        prefs = real_loader.load_room_preferences()
        assert len(prefs) > 0

    def test_validate_stage1_real_data(self, real_loader):
        """Validate all Stage 1 data together."""
        warnings = real_loader.validate_stage1()
        # May have warnings but shouldn't raise errors
        assert isinstance(warnings, list)


class TestDataLoaderStage2:
    """Tests for Stage 2 data loading."""

    @pytest.fixture
    def real_loader(self) -> "DataLoader":
        """Create loader with real V4 data if available."""
        from timetable.core.loader import DataLoader

        v4_path = Path(__file__).parent.parent.parent / "stage_2"
        if v4_path.exists():
            return DataLoader(v4_path.parent)
        pytest.skip("Real V4 data not available")

    def test_load_faculty_full(self, real_loader):
        """Load full faculty data from Stage 2."""
        faculty = real_loader.load_faculty_full()
        assert len(faculty) >= 10
        # Check that full data has workload stats
        for f in faculty:
            assert f.workload_stats is not None
            assert f.workload_stats.total_weekly_hours >= 0

    def test_load_subjects_full(self, real_loader):
        """Load full subject data from Stage 2."""
        subjects = real_loader.load_subjects_full()
        assert len(subjects) >= 10
        # Check that subjects have components
        core_subjects = [s for s in subjects if s.type == "core"]
        assert len(core_subjects) > 0
        # Core subjects should have components
        for s in core_subjects:
            if s.total_credits > 0:
                assert len(s.components) > 0

    def test_load_all_stage2(self, real_loader):
        """Load all Stage 2 data at once."""
        data = real_loader.load_all_stage2()
        assert "faculty_full" in data
        assert "subjects_full" in data
        assert len(data["faculty_full"]) > 0
        assert len(data["subjects_full"]) > 0


class TestDataLoaderStage3:
    """Tests for Stage 3 data loading."""

    @pytest.fixture
    def real_loader(self) -> "DataLoader":
        """Create loader with real V4 data if available."""
        from timetable.core.loader import DataLoader

        v4_path = Path(__file__).parent.parent.parent / "stage_3"
        if v4_path.exists():
            return DataLoader(v4_path.parent)
        pytest.skip("Real V4 data not available")

    def test_load_teaching_assignments_sem1(self, real_loader):
        """Load Semester 1 teaching assignments."""
        assignments_file = real_loader.load_teaching_assignments(1)
        assert assignments_file.metadata.semester == 1
        assert len(assignments_file.assignments) > 0
        # Check assignment structure
        for a in assignments_file.assignments:
            assert a.assignment_id
            assert a.faculty_id
            assert len(a.student_group_ids) > 0

    def test_load_teaching_assignments_sem3(self, real_loader):
        """Load Semester 3 teaching assignments."""
        assignments_file = real_loader.load_teaching_assignments(3)
        assert assignments_file.metadata.semester == 3
        assert len(assignments_file.assignments) > 0

    def test_load_all_teaching_assignments(self, real_loader):
        """Load all teaching assignments."""
        all_assignments = real_loader.load_all_teaching_assignments()
        assert 1 in all_assignments
        assert 3 in all_assignments
        total = sum(len(af.assignments) for af in all_assignments.values())
        assert total > 30  # Should have 45 total

    def test_load_overlap_constraints(self, real_loader):
        """Load student group overlap constraints."""
        constraints = real_loader.load_overlap_constraints()
        assert len(constraints.cannot_overlap_with) > 0
        assert len(constraints.can_run_parallel_with) > 0
        # Check known constraint
        assert "MCA_SEM1_A" in constraints.cannot_overlap_with

    def test_load_statistics(self, real_loader):
        """Load statistics file."""
        stats = real_loader.load_statistics()
        assert stats.semester1 is not None
        assert stats.semester3 is not None
        assert stats.combined is not None
        # Check combined stats
        assert stats.combined.total_assignments > 0

    def test_load_all_stage3(self, real_loader):
        """Load all Stage 3 data at once."""
        data = real_loader.load_all_stage3()
        assert "assignments" in data
        assert "overlap_constraints" in data
        assert "statistics" in data
        assert 1 in data["assignments"]


class TestConvenienceFunctionsStage2And3:
    """Tests for Stage 2 and Stage 3 convenience functions."""

    def test_load_faculty_full_function(self):
        """load_faculty_full should load faculty2Full.json."""
        from timetable.core.loader import load_faculty_full

        v4_path = Path(__file__).parent.parent.parent / "stage_2" / "faculty2Full.json"
        if not v4_path.exists():
            pytest.skip("Real V4 data not available")

        faculty = load_faculty_full(v4_path)
        assert len(faculty) > 0

    def test_load_subjects_full_function(self):
        """load_subjects_full should load subjects2Full.json."""
        from timetable.core.loader import load_subjects_full

        v4_path = Path(__file__).parent.parent.parent / "stage_2" / "subjects2Full.json"
        if not v4_path.exists():
            pytest.skip("Real V4 data not available")

        subjects = load_subjects_full(v4_path)
        assert len(subjects) > 0

    def test_load_teaching_assignments_function(self):
        """load_teaching_assignments should load assignment files."""
        from timetable.core.loader import load_teaching_assignments

        v4_path = Path(__file__).parent.parent.parent / "stage_3" / "teachingAssignments_sem1.json"
        if not v4_path.exists():
            pytest.skip("Real V4 data not available")

        assignments = load_teaching_assignments(v4_path)
        assert len(assignments.assignments) > 0

    def test_load_overlap_constraints_function(self):
        """load_overlap_constraints should load constraint file."""
        from timetable.core.loader import load_overlap_constraints

        v4_path = Path(__file__).parent.parent.parent / "stage_3" / "studentGroupOverlapConstraints.json"
        if not v4_path.exists():
            pytest.skip("Real V4 data not available")

        constraints = load_overlap_constraints(v4_path)
        assert len(constraints.cannot_overlap_with) > 0

    def test_load_statistics_function(self):
        """load_statistics should load statistics.json."""
        from timetable.core.loader import load_statistics

        v4_path = Path(__file__).parent.parent.parent / "stage_3" / "statistics.json"
        if not v4_path.exists():
            pytest.skip("Real V4 data not available")

        stats = load_statistics(v4_path)
        assert stats.combined.total_assignments > 0
