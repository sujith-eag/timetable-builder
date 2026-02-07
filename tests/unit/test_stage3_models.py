"""
Tests for Stage 3 Pydantic models.

Tests cover:
- TeachingAssignment and AssignmentConstraints models
- TeachingAssignmentsFile with metadata and statistics
- StudentGroupOverlapConstraints
- Statistics models (SemesterStats, CombinedStats, etc.)
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from timetable.models.stage3 import (
    AssignmentConstraints,
    AssignmentMetadata,
    AssignmentStatistics,
    CombinedStats,
    ComponentStats,
    ConstraintStats,
    FacultyDistributionEntry,
    FacultyWorkloadEntry,
    PriorityStats,
    ResourceAnalysis,
    RoomRequirementStats,
    RoomTypeStats,
    SemesterStats,
    StatisticsFile,
    StatisticsMetadata,
    StudentGroupOverlapConstraints,
    StudentGroupStatsEntry,
    SubjectCoverageEntry,
    TeachingAssignment,
    TeachingAssignmentsFile,
    TypeStats,
)


# ==================== TeachingAssignment Tests ====================


class TestAssignmentConstraints:
    """Tests for AssignmentConstraints model."""

    def test_valid_constraints(self):
        """Test valid constraints creation."""
        constraints = AssignmentConstraints(
            studentGroupConflicts=["MCA_SEM1_A"],
            facultyConflicts=["MM"],
            fixedDay=None,
            fixedSlot=None,
            mustBeInRoom=None,
        )
        assert constraints.student_group_conflicts == ["MCA_SEM1_A"]
        assert constraints.faculty_conflicts == ["MM"]
        assert constraints.fixed_day is None

    def test_constraints_with_fixed_timing(self):
        """Test constraints with fixed day and slot."""
        constraints = AssignmentConstraints(
            studentGroupConflicts=["MCA_SEM3_A"],
            facultyConflicts=["SA"],
            fixedDay="Tue",
            fixedSlot="S6",
            mustBeInRoom="LAB-1",
        )
        assert constraints.fixed_day == "Tue"
        assert constraints.fixed_slot == "S6"
        assert constraints.must_be_in_room == "LAB-1"


class TestTeachingAssignment:
    """Tests for TeachingAssignment model."""

    @pytest.fixture
    def sample_assignment(self):
        """Create a sample teaching assignment."""
        return TeachingAssignment(
            assignmentId="TA_25MCA15_TH_B_001",
            subjectCode="25MCA15",
            shortCode="DS",
            subjectTitle="Data Structures",
            componentId="25MCA15_TH",
            componentType="theory",
            semester=1,
            facultyId="MM",
            facultyName="Dr M. Manjunath",
            studentGroupIds=["MCA_SEM1_B"],
            sections=["B"],
            sessionDuration=55,
            sessionsPerWeek=3,
            requiresRoomType="lecture",
            preferredRooms=[],
            requiresContiguous=False,
            blockSizeSlots=1,
            priority="high",
            isElective=False,
            isDiffSubject=False,
            constraints=AssignmentConstraints(
                studentGroupConflicts=["MCA_SEM1_B"],
                facultyConflicts=["MM"],
                fixedDay=None,
                fixedSlot=None,
                mustBeInRoom=None,
            ),
        )

    def test_valid_assignment(self, sample_assignment):
        """Test valid assignment creation."""
        assert sample_assignment.assignment_id == "TA_25MCA15_TH_B_001"
        assert sample_assignment.subject_code == "25MCA15"
        assert sample_assignment.component_type == "theory"
        assert sample_assignment.faculty_id == "MM"
        assert sample_assignment.session_duration == 55
        assert sample_assignment.sessions_per_week == 3
        assert not sample_assignment.requires_contiguous

    def test_weekly_hours_property(self, sample_assignment):
        """Test weekly_hours computed property."""
        # 55 minutes * 3 sessions / 60 = 2.75 hours
        assert sample_assignment.weekly_hours == pytest.approx(2.75, rel=0.01)

    def test_is_lab_session_property(self, sample_assignment):
        """Test is_lab_session property."""
        assert not sample_assignment.is_lab_session

        # Create a lab assignment
        lab_assignment = TeachingAssignment(
            assignmentId="TA_25MCA11_PR_A_001",
            subjectCode="25MCA11",
            shortCode="PwP",
            subjectTitle="Programming with Python",
            componentId="25MCA11_PR",
            componentType="practical",
            semester=1,
            facultyId="SM",
            facultyName="Ms Swathi M",
            studentGroupIds=["MCA_SEM1_A"],
            sections=["A"],
            sessionDuration=110,
            sessionsPerWeek=1,
            requiresRoomType="lab",
            preferredRooms=[],
            requiresContiguous=True,
            blockSizeSlots=2,
            priority="high",
            isElective=False,
            isDiffSubject=False,
            constraints=AssignmentConstraints(
                studentGroupConflicts=["MCA_SEM1_A"],
                facultyConflicts=["SM"],
            ),
        )
        assert lab_assignment.is_lab_session

    def test_invalid_component_type(self):
        """Test invalid component type is rejected."""
        with pytest.raises(ValidationError):
            TeachingAssignment(
                assignmentId="TA_TEST",
                subjectCode="TEST",
                shortCode="T",
                subjectTitle="Test",
                componentId="TEST_XX",
                componentType="invalid",  # Invalid
                semester=1,
                facultyId="XX",
                facultyName="Test",
                studentGroupIds=["TEST"],
                sections=["A"],
                sessionDuration=55,
                sessionsPerWeek=1,
                requiresRoomType="lecture",
                requiresContiguous=False,
                blockSizeSlots=1,
                priority="high",
                isElective=False,
                isDiffSubject=False,
                constraints=AssignmentConstraints(),
            )

    def test_invalid_priority(self):
        """Test invalid priority is rejected."""
        with pytest.raises(ValidationError):
            TeachingAssignment(
                assignmentId="TA_TEST",
                subjectCode="TEST",
                shortCode="T",
                subjectTitle="Test",
                componentId="TEST_TH",
                componentType="theory",
                semester=1,
                facultyId="XX",
                facultyName="Test",
                studentGroupIds=["TEST"],
                sections=["A"],
                sessionDuration=55,
                sessionsPerWeek=1,
                requiresRoomType="lecture",
                requiresContiguous=False,
                blockSizeSlots=1,
                priority="urgent",  # Invalid
                isElective=False,
                isDiffSubject=False,
                constraints=AssignmentConstraints(),
            )


# ==================== TeachingAssignmentsFile Tests ====================


class TestTeachingAssignmentsFile:
    """Tests for TeachingAssignmentsFile model."""

    @pytest.fixture
    def sample_assignments_file(self):
        """Create a sample assignments file."""
        assignments = [
            TeachingAssignment(
                assignmentId="TA_25MCA15_TH_A_001",
                subjectCode="25MCA15",
                shortCode="DS",
                subjectTitle="Data Structures",
                componentId="25MCA15_TH",
                componentType="theory",
                semester=1,
                facultyId="SM",
                facultyName="Ms Swathi M",
                studentGroupIds=["MCA_SEM1_A"],
                sections=["A"],
                sessionDuration=55,
                sessionsPerWeek=3,
                requiresRoomType="lecture",
                preferredRooms=[],
                requiresContiguous=False,
                blockSizeSlots=1,
                priority="high",
                isElective=False,
                isDiffSubject=False,
                constraints=AssignmentConstraints(
                    studentGroupConflicts=["MCA_SEM1_A"],
                    facultyConflicts=["SM"],
                ),
            ),
            TeachingAssignment(
                assignmentId="TA_25MCA15_TH_B_002",
                subjectCode="25MCA15",
                shortCode="DS",
                subjectTitle="Data Structures",
                componentId="25MCA15_TH",
                componentType="theory",
                semester=1,
                facultyId="MM",
                facultyName="Dr M. Manjunath",
                studentGroupIds=["MCA_SEM1_B"],
                sections=["B"],
                sessionDuration=55,
                sessionsPerWeek=3,
                requiresRoomType="lecture",
                preferredRooms=[],
                requiresContiguous=False,
                blockSizeSlots=1,
                priority="high",
                isElective=False,
                isDiffSubject=False,
                constraints=AssignmentConstraints(
                    studentGroupConflicts=["MCA_SEM1_B"],
                    facultyConflicts=["MM"],
                ),
            ),
        ]
        return TeachingAssignmentsFile(
            metadata=AssignmentMetadata(
                semester=1,
                generatedAt=datetime.now(),
                totalAssignments=2,
                generator="test",
            ),
            assignments=assignments,
            statistics=AssignmentStatistics(
                totalAssignments=2,
                byType={"core": 2},
                byComponentType={"theory": 2},
                byPriority={"high": 2},
                totalSessions=6,
                totalWeeklyHours=5.5,
                facultyAssignments={"SM": 1, "MM": 1},
                roomRequirements={"lecture": 2},
                withFixedTiming=0,
                withPreAllocatedRooms=0,
                withRoomPreferences=0,
            ),
        )

    def test_get_assignment(self, sample_assignments_file):
        """Test get_assignment method."""
        assign = sample_assignments_file.get_assignment("TA_25MCA15_TH_A_001")
        assert assign is not None
        assert assign.faculty_id == "SM"

        missing = sample_assignments_file.get_assignment("MISSING")
        assert missing is None

    def test_get_assignments_for_faculty(self, sample_assignments_file):
        """Test get_assignments_for_faculty method."""
        sm_assigns = sample_assignments_file.get_assignments_for_faculty("SM")
        assert len(sm_assigns) == 1
        assert sm_assigns[0].sections == ["A"]

    def test_get_assignments_for_subject(self, sample_assignments_file):
        """Test get_assignments_for_subject method."""
        ds_assigns = sample_assignments_file.get_assignments_for_subject("25MCA15")
        assert len(ds_assigns) == 2

    def test_get_assignments_for_group(self, sample_assignments_file):
        """Test get_assignments_for_group method."""
        grp_assigns = sample_assignments_file.get_assignments_for_group("MCA_SEM1_A")
        assert len(grp_assigns) == 1
        assert grp_assigns[0].faculty_id == "SM"

    def test_get_theory_assignments(self, sample_assignments_file):
        """Test get_theory_assignments method."""
        theory = sample_assignments_file.get_theory_assignments()
        assert len(theory) == 2

    def test_get_lab_assignments(self, sample_assignments_file):
        """Test get_lab_assignments method."""
        labs = sample_assignments_file.get_lab_assignments()
        assert len(labs) == 0  # Both are lecture


# ==================== StudentGroupOverlapConstraints Tests ====================


class TestStudentGroupOverlapConstraints:
    """Tests for StudentGroupOverlapConstraints model."""

    @pytest.fixture
    def sample_constraints(self):
        """Create sample overlap constraints."""
        return StudentGroupOverlapConstraints(
            cannotOverlapWith={
                "MCA_SEM1_A": ["MCA_SEM1_A"],
                "MCA_SEM1_B": ["MCA_SEM1_B"],
                "MCA_SEM3_A": ["ELEC_AD_A1", "ELEC_SS_G1", "MCA_SEM3_A"],
                "ELEC_AD_A1": ["ELEC_AD_A1", "MCA_SEM3_A"],
            },
            canRunParallelWith={
                "MCA_SEM1_A": ["MCA_SEM1_B"],
                "MCA_SEM1_B": ["MCA_SEM1_A"],
                "ELEC_AD_A1": ["ELEC_AD_B1", "ELEC_SS_G1"],
            },
        )

    def test_get_conflicts_for_group(self, sample_constraints):
        """Test get_conflicts_for_group method."""
        conflicts = sample_constraints.get_conflicts_for_group("MCA_SEM3_A")
        assert "ELEC_AD_A1" in conflicts
        assert "ELEC_SS_G1" in conflicts
        assert "MCA_SEM3_A" in conflicts

        # Non-existent group
        empty = sample_constraints.get_conflicts_for_group("UNKNOWN")
        assert empty == []

    def test_get_parallel_groups(self, sample_constraints):
        """Test get_parallel_groups method."""
        parallel = sample_constraints.get_parallel_groups("MCA_SEM1_A")
        assert parallel == ["MCA_SEM1_B"]

        parallel = sample_constraints.get_parallel_groups("ELEC_AD_A1")
        assert "ELEC_AD_B1" in parallel
        assert "ELEC_SS_G1" in parallel

    def test_can_schedule_together(self, sample_constraints):
        """Test can_schedule_together method."""
        # Same groups cannot be scheduled together
        assert not sample_constraints.can_schedule_together(
            "MCA_SEM1_A", "MCA_SEM1_A"
        )

        # Different sections can be scheduled together (parallel)
        assert sample_constraints.can_schedule_together(
            "MCA_SEM1_A", "MCA_SEM1_B"
        )

        # MCA_SEM3_A and ELEC_AD_A1 conflict
        assert not sample_constraints.can_schedule_together(
            "MCA_SEM3_A", "ELEC_AD_A1"
        )


# ==================== Statistics Models Tests ====================


class TestComponentStats:
    """Tests for ComponentStats model."""

    def test_valid_component_stats(self):
        """Test valid component stats creation."""
        stats = ComponentStats(count=10, sessions=28, hours=25.66)
        assert stats.count == 10
        assert stats.sessions == 28
        assert stats.hours == pytest.approx(25.66, rel=0.01)


class TestFacultyDistributionEntry:
    """Tests for FacultyDistributionEntry model."""

    def test_valid_entry(self):
        """Test valid faculty distribution entry."""
        entry = FacultyDistributionEntry(
            facultyName="Dr M. Manjunath",
            assignments=2,
            sessions=4,
            hours=4.58,
            subjects=["25MCA15", "25MCA16"],
            subjectCount=2,
            components={"theory": 1, "practical": 1},
        )
        assert entry.faculty_name == "Dr M. Manjunath"
        assert entry.assignments == 2
        assert len(entry.subjects) == 2


class TestSubjectCoverageEntry:
    """Tests for SubjectCoverageEntry model."""

    def test_valid_entry(self):
        """Test valid subject coverage entry."""
        entry = SubjectCoverageEntry(
            title="Data Structures",
            faculty=["MM", "SM"],
            facultyCount=2,
            components=["theory", "theory"],
            componentCount=2,
            totalSessions=6,
            sections=["A", "B"],
        )
        assert entry.title == "Data Structures"
        assert entry.faculty_count == 2
        assert entry.total_sessions == 6


class TestConstraintStats:
    """Tests for ConstraintStats model."""

    def test_valid_constraint_stats(self):
        """Test valid constraint stats creation."""
        stats = ConstraintStats(
            withStudentConflicts=24,
            withFacultyConflicts=24,
            withFixedTiming=0,
            withRoomAllocation=0,
            withRoomPreferences=0,
            withContiguousRequirement=14,
        )
        assert stats.with_student_conflicts == 24
        assert stats.with_contiguous_requirement == 14


class TestResourceAnalysis:
    """Tests for ResourceAnalysis model."""

    def test_valid_resource_analysis(self):
        """Test valid resource analysis creation."""
        analysis = ResourceAnalysis(
            lectureRoomSessions=44,
            labSessions=37,
            theorySessions=44,
            practicalSessions=29,
            tutorialSessions=8,
        )
        assert analysis.lecture_room_sessions == 44
        assert analysis.lab_sessions == 37
        assert analysis.theory_sessions == 44


# ==================== Full Statistics File Test ====================


class TestStatisticsFile:
    """Tests for StatisticsFile model."""

    @pytest.fixture
    def minimal_semester_stats(self):
        """Create minimal semester stats for testing."""
        return SemesterStats(
            semester=1,
            totalAssignments=24,
            totalSessions=44,
            totalHours=55.0,
            byType={"core": TypeStats(count=24, sessions=44)},
            byComponent={"theory": ComponentStats(count=10, sessions=28, hours=25.66)},
            byPriority={"high": PriorityStats(count=24, sessions=44)},
            byRoomType={"lecture": RoomTypeStats(count=10, sessions=28)},
            facultyDistribution={
                "MM": FacultyDistributionEntry(
                    facultyName="Dr M. Manjunath",
                    assignments=2,
                    sessions=4,
                    hours=4.58,
                    subjects=["25MCA15"],
                    subjectCount=1,
                    components={"theory": 1},
                )
            },
            subjectCoverage={
                "25MCA15": SubjectCoverageEntry(
                    title="Data Structures",
                    faculty=["MM"],
                    facultyCount=1,
                    components=["theory"],
                    componentCount=1,
                    totalSessions=3,
                    sections=["B"],
                )
            },
            studentGroups={
                "MCA_SEM1_A": StudentGroupStatsEntry(
                    assignments=12,
                    sessions=22,
                    hours=27.48,
                    subjects=["25MCA15"],
                    subjectCount=1,
                )
            },
            constraints=ConstraintStats(
                withStudentConflicts=24,
                withFacultyConflicts=24,
                withFixedTiming=0,
                withRoomAllocation=0,
                withRoomPreferences=0,
                withContiguousRequirement=14,
            ),
            conflictPatterns={"1": 24},
            roomRequirements=RoomRequirementStats(
                uniqueRoomsNeeded=0,
                preAllocatedRooms=[],
                preferredRoomsList=[],
            ),
        )

    def test_get_semester_stats(self, minimal_semester_stats):
        """Test get_semester_stats method."""
        stats_file = StatisticsFile(
            metadata=StatisticsMetadata(
                generatedAt=datetime.now(),
                generator="test",
                version="1.0",
            ),
            semester1=minimal_semester_stats,
            semester3=minimal_semester_stats,  # Reuse for testing
            combined=CombinedStats(
                totalAssignments=48,
                totalSessions=88,
                totalHours=110.0,
                facultyWorkload={},
                resourceAnalysis=ResourceAnalysis(
                    lectureRoomSessions=44,
                    labSessions=37,
                    theorySessions=44,
                    practicalSessions=29,
                    tutorialSessions=8,
                ),
            ),
        )

        sem1 = stats_file.get_semester_stats(1)
        assert sem1 is not None
        assert sem1.semester == 1

        sem3 = stats_file.get_semester_stats(3)
        assert sem3 is not None

        sem2 = stats_file.get_semester_stats(2)
        assert sem2 is None
