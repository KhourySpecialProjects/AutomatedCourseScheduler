from dataclasses import dataclass, field

from app.schemas.section import CoursePreferenceInfo, MeetingPreferenceInfo
from app.schemas.warning import Warning


@dataclass(frozen=True)
class MatchedAssignment:
    """Represents a course section assigned to a faculty member
    during the scheduling algorithm."""

    section_id: int
    course_id: int
    faculty_nuid: int
    department_code: str


@dataclass
class SectionAssignment:
    """Represents a section and instructor with a chosen time block and time preference level
    during the scheduling algorithm."""

    section_id: int
    faculty_nuid: int
    time_block_id: int | None
    time_preference_level: int | None


@dataclass
class TimeBlockAssignmentResult:
    """Represents time block placements and warnings produced
    during the scheduling algorithm."""

    assignments: list[SectionAssignment]
    warnings: list[Warning]


@dataclass
class SectionCandidate:
    """Represents a potential assignment of a course section to a faculty member
    during the scheduling algorithm."""

    course_id: int
    section_id: int
    time_block_id: int | None = None
    is_priority: bool = False
    seen_second_pass: bool = False
    assigned_faculty_nuid: int | None = None
    assigned_pref_level: int | None = None


@dataclass
class FacultyState:
    """Represents the current state of a faculty member during the scheduling algorithm."""

    nuid: int
    max_load: int
    course_preferences: list[CoursePreferenceInfo] = field(default_factory=list)
    time_preferences: list[MeetingPreferenceInfo] = field(default_factory=list)
    current_load: int = 0
    assigned_time_blocks: set[int] = field(default_factory=set)


@dataclass
class CourseAssignment:
    section_id: int
    course_id: int
    department_code: str = ""
    faculty_nuid: int | None = None
    assigned_pref_level: int | None = None
    is_matched: bool = False
    unmatched_reason: str | None = None
