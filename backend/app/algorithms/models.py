from dataclasses import dataclass, field

from app.schemas.section import CoursePreferenceInfo, MeetingPreferenceInfo


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
    faculty_nuid: int | None = None
    assigned_pref_level: int | None = None
    is_matched: bool = False
    unmatched_reason: str | None = None
