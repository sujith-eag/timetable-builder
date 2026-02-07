"""
Unit tests for Stage 1 Pydantic models.

Tests cover validation, serialization, and helper methods.
"""

import pytest
from pydantic import ValidationError


class TestTimeSlot:
    """Tests for TimeSlot model."""

    def test_valid_time_slot(self):
        """TimeSlot should accept valid data."""
        from timetable.models.stage1 import TimeSlot

        slot = TimeSlot(
            slotId="S1",
            start="09:00",
            end="09:55",
            lengthMinutes=55,
        )
        assert slot.slot_id == "S1"
        assert slot.start == "09:00"
        assert slot.end == "09:55"
        assert slot.length_minutes == 55

    def test_invalid_time_format(self):
        """TimeSlot should reject invalid time formats."""
        from timetable.models.stage1 import TimeSlot

        with pytest.raises(ValidationError) as exc_info:
            TimeSlot(slotId="S1", start="9:00", end="9AM", lengthMinutes=55)
        assert "time" in str(exc_info.value).lower()

    def test_negative_duration(self):
        """TimeSlot should reject negative duration."""
        from timetable.models.stage1 import TimeSlot

        with pytest.raises(ValidationError):
            TimeSlot(slotId="S1", start="09:00", end="09:55", lengthMinutes=-10)

    def test_alias_mapping(self):
        """TimeSlot should map aliases correctly."""
        from timetable.models.stage1 import TimeSlot

        data = {"slotId": "S1", "start": "09:00", "end": "09:55", "lengthMinutes": 55}
        slot = TimeSlot.model_validate(data)
        assert slot.slot_id == "S1"


class TestSubject:
    """Tests for Subject model."""

    def test_valid_subject(self):
        """Subject should accept valid data."""
        from timetable.models.stage1 import Subject

        subject = Subject(
            subjectCode="25MCA11",
            shortCode="PwP",
            title="Programming with Python",
            creditPattern=[3, 0, 1],
            totalCredits=4,
            department="MCA",
            semester=1,
            isElective=False,
            type="core",
        )
        assert subject.subject_code == "25MCA11"
        assert subject.total_credits == 4
        assert subject.has_theory is True
        assert subject.has_tutorial is False
        assert subject.has_practical is True

    def test_credit_pattern_validation(self):
        """Subject should validate credit pattern correctly."""
        from timetable.models.stage1 import Subject

        # Wrong number of elements
        with pytest.raises(ValidationError):
            Subject(
                subjectCode="CS101",
                shortCode="CS",
                title="Test",
                creditPattern=[3, 0],  # Only 2 elements
                totalCredits=3,
                department="MCA",
                semester=1,
                isElective=False,
                type="core",
            )

    def test_total_credits_mismatch(self):
        """Subject should reject mismatched total credits."""
        from timetable.models.stage1 import Subject

        with pytest.raises(ValidationError) as exc_info:
            Subject(
                subjectCode="CS101",
                shortCode="CS",
                title="Test",
                creditPattern=[3, 0, 1],
                totalCredits=5,  # Should be 4
                department="MCA",
                semester=1,
                isElective=False,
                type="core",
            )
        assert "doesn't match" in str(exc_info.value).lower()

    def test_credit_properties(self):
        """Subject should expose credit properties."""
        from timetable.models.stage1 import Subject

        subject = Subject(
            subjectCode="CS101",
            shortCode="CS",
            title="Test",
            creditPattern=[2, 1, 3],
            totalCredits=6,
            department="MCA",
            semester=1,
            isElective=False,
            type="core",
        )
        assert subject.theory_credits == 2
        assert subject.tutorial_credits == 1
        assert subject.practical_credits == 3

    def test_subject_type_validation(self):
        """Subject should validate type field."""
        from timetable.models.stage1 import Subject

        with pytest.raises(ValidationError):
            Subject(
                subjectCode="CS101",
                shortCode="CS",
                title="Test",
                creditPattern=[3, 0, 1],
                totalCredits=4,
                department="MCA",
                semester=1,
                isElective=False,
                type="invalid",  # Should be 'core' or 'elective'
            )


class TestFaculty:
    """Tests for Faculty model."""

    def test_valid_faculty(self):
        """Faculty should accept valid data."""
        from timetable.models.stage1 import Faculty

        faculty = Faculty(
            facultyId="SA",
            name="Dr S. Ajitha",
            designation="Professor",
            assignedSubjects=[{"24MCA31": ["B"]}],
            supportingSubjects=["24MCASS5"],
        )
        assert faculty.faculty_id == "SA"
        assert faculty.name == "Dr S. Ajitha"

    def test_get_all_subject_codes(self):
        """Faculty should return all subject codes."""
        from timetable.models.stage1 import Faculty

        faculty = Faculty(
            facultyId="MM",
            name="Dr M. Manjunath",
            designation="Associate Professor",
            assignedSubjects=[
                "24MCAAD1",
                {"25MCA15": ["B"]},
                {"25MCA16": ["B"]},
            ],
            supportingSubjects=["25MCA17"],
        )
        codes = faculty.get_all_subject_codes()
        assert "24MCAAD1" in codes
        assert "25MCA15" in codes
        assert "25MCA16" in codes
        assert "25MCA17" in codes

    def test_empty_assignments(self):
        """Faculty should accept empty assignments."""
        from timetable.models.stage1 import Faculty

        faculty = Faculty(
            facultyId="NEW",
            name="New Faculty",
            designation="Lecturer",
        )
        assert faculty.assigned_subjects == []
        assert faculty.supporting_subjects == []


class TestStudentGroup:
    """Tests for StudentGroup model."""

    def test_valid_student_group(self):
        """StudentGroup should accept valid data."""
        from timetable.models.stage1 import StudentGroup

        group = StudentGroup(
            semester=1,
            section="A",
            studentCount=60,
            studentGroupId="MCA_SEM1_A",
            compulsorySubjects=["25MCA11", "25MCA12"],
        )
        assert group.student_group_id == "MCA_SEM1_A"
        assert group.student_count == 60

    def test_invalid_semester(self):
        """StudentGroup should reject invalid semester."""
        from timetable.models.stage1 import StudentGroup

        with pytest.raises(ValidationError):
            StudentGroup(
                semester=0,  # Invalid
                section="A",
                studentCount=60,
                studentGroupId="TEST",
            )


class TestConfig:
    """Tests for Config model."""

    def test_full_config(self, sample_config):
        """Config should load complete configuration."""
        from timetable.models.stage1 import ConfigFile

        config_file = ConfigFile.model_validate(sample_config)
        config = config_file.config

        assert len(config.time_slots) == 7
        assert len(config.weekdays) == 6
        assert len(config.resources.rooms) > 0

    def test_get_slot(self, sample_config):
        """Config should find slots by ID."""
        from timetable.models.stage1 import ConfigFile

        config = ConfigFile.model_validate(sample_config).config
        
        slot = config.get_slot("S1")
        assert slot is not None
        assert slot.slot_id == "S1"
        
        assert config.get_slot("INVALID") is None

    def test_resources_methods(self, sample_config):
        """Resources should provide helper methods."""
        from timetable.models.stage1 import ConfigFile

        config = ConfigFile.model_validate(sample_config).config
        
        lecture_rooms = config.resources.get_rooms_by_type("lecture")
        assert len(lecture_rooms) > 0
        
        lab_rooms = config.resources.get_rooms_by_type("lab")
        assert len(lab_rooms) > 0


class TestRoomPreference:
    """Tests for RoomPreference model."""

    def test_valid_room_preference(self):
        """RoomPreference should accept valid data."""
        from timetable.models.stage1 import RoomPreference

        pref = RoomPreference(
            subjectCode="24MCA32",
            componentType="practical",
            semester=3,
            studentGroupId="MCA_SEM3_A",
            preferredRooms=["LAB-1"],
            roomAllocations={"24MCA32_PR_A": "LAB-1"},
        )
        assert pref.subject_code == "24MCA32"
        assert pref.component_type == "practical"

    def test_invalid_component_type(self):
        """RoomPreference should reject invalid component types."""
        from timetable.models.stage1 import RoomPreference

        with pytest.raises(ValidationError):
            RoomPreference(
                subjectCode="CS101",
                componentType="invalid",  # Should be theory/tutorial/practical
                semester=1,
                studentGroupId="GROUP1",
                preferredRooms=["ROOM1"],
            )


class TestStudentGroupFile:
    """Tests for StudentGroupFile model."""

    def test_full_student_group_file(self, sample_student_groups):
        """StudentGroupFile should load all group types."""
        from timetable.models.stage1 import StudentGroupFile

        groups_file = StudentGroupFile.model_validate(sample_student_groups)
        
        assert len(groups_file.student_groups) > 0

    def test_get_group_method(self):
        """StudentGroupFile should find groups by ID."""
        from timetable.models.stage1 import StudentGroupFile

        data = {
            "studentGroups": [
                {
                    "semester": 1,
                    "section": "A",
                    "studentCount": 60,
                    "studentGroupId": "MCA_SEM1_A",
                    "compulsorySubjects": [],
                }
            ],
            "electiveSubjectGroups": [],
            "electiveStudentGroups": [],
            "groupHierarchy": {},
        }
        groups_file = StudentGroupFile.model_validate(data)
        
        group = groups_file.get_group("MCA_SEM1_A")
        assert group is not None
        assert group.section == "A"
        
        assert groups_file.get_group("INVALID") is None


class TestModelSerialization:
    """Tests for model serialization."""

    def test_subject_to_dict(self):
        """Subject should serialize to dictionary."""
        from timetable.models.stage1 import Subject

        subject = Subject(
            subjectCode="CS101",
            shortCode="CS",
            title="Test",
            creditPattern=[3, 0, 1],
            totalCredits=4,
            department="MCA",
            semester=1,
            isElective=False,
            type="core",
        )
        data = subject.model_dump(by_alias=True)
        
        assert data["subjectCode"] == "CS101"
        assert data["creditPattern"] == [3, 0, 1]

    def test_config_round_trip(self, sample_config):
        """Config should survive JSON round-trip."""
        import json

        from timetable.models.stage1 import ConfigFile

        config_file = ConfigFile.model_validate(sample_config)
        
        # Serialize and deserialize
        json_str = config_file.model_dump_json(by_alias=True)
        data = json.loads(json_str)
        config_file2 = ConfigFile.model_validate(data)
        
        assert config_file2.config.day_start == config_file.config.day_start
