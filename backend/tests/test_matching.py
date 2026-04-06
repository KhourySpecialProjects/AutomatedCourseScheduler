"""Tests for get_eligible_ranked_faculty in app/algorithms/matching.py"""

from app.algorithms.matching import get_eligible_ranked_faculty
from app.algorithms.models import FacultyState, SectionCandidate
from app.schemas.section import CoursePreferenceInfo, MeetingPreferenceInfo

# ---------------------
# Helpers
# ---------------------


def make_section(
    section_id: int = 1,
    course_id: int = 100,
    time_block_id: int = 10,
    is_priority: bool = False,
) -> SectionCandidate:
    return SectionCandidate(
        section_id=section_id,
        course_id=course_id,
        time_block_id=time_block_id,
        is_priority=is_priority,
    )


def make_faculty(
    nuid: int = 1,
    max_load: int = 3,
    current_load: int = 0,
    course_id: int = 100,
    course_pref: str = "Eager to teach",
    time_block_id: int = 10,
    time_pref: str = "Eager to teach",
    assigned_time_blocks: set[int] | None = None,
) -> FacultyState:
    return FacultyState(
        nuid=nuid,
        max_load=max_load,
        current_load=current_load,
        course_preferences=[
            CoursePreferenceInfo(
                course_id=course_id,
                course_name="Test Course",
                preference=course_pref,
            )
        ],
        time_preferences=[
            MeetingPreferenceInfo(
                time_block_id=time_block_id,
                preference=time_pref,
            )
        ],
        assigned_time_blocks=assigned_time_blocks or set(),
    )


# ---------------------
# Hard exclude: NOT_INTERESTED
# ---------------------


def test_not_interested_is_excluded():
    section = make_section()
    faculty = make_faculty(course_pref="Not my cup of tea")
    result = get_eligible_ranked_faculty(section, [faculty])
    assert result == []


# ---------------------
# Hard exclude: unrated course
# ---------------------


def test_unrated_course_is_excluded():
    section = make_section(course_id=100)
    faculty = FacultyState(
        nuid=1,
        max_load=3,
        current_load=0,
        course_preferences=[
            CoursePreferenceInfo(
                course_id=999,  # different course — no entry for 100
                course_name="Other Course",
                preference="Eager to teach",
            )
        ],
        time_preferences=[],
        assigned_time_blocks=set(),
    )
    result = get_eligible_ranked_faculty(section, [faculty])
    assert result == []


# ---------------------
# Hard exclude: over capacity
# ---------------------


def test_at_max_load_is_excluded():
    section = make_section()
    faculty = make_faculty(max_load=2, current_load=2)
    result = get_eligible_ranked_faculty(section, [faculty])
    assert result == []


def test_under_max_load_is_included():
    section = make_section()
    faculty = make_faculty(max_load=3, current_load=2)
    result = get_eligible_ranked_faculty(section, [faculty])
    assert result == [faculty]


# ---------------------
# Hard exclude: time block conflict
# ---------------------


def test_time_block_conflict_is_excluded():
    section = make_section(time_block_id=10)
    faculty = make_faculty(assigned_time_blocks={10})
    result = get_eligible_ranked_faculty(section, [faculty])
    assert result == []


def test_no_time_block_conflict_is_included():
    section = make_section(time_block_id=10)
    faculty = make_faculty(assigned_time_blocks={20, 30})
    result = get_eligible_ranked_faculty(section, [faculty])
    assert result == [faculty]


# ---------------------
# Ranking: course preference
# ---------------------


def test_ranked_by_course_preference():
    section = make_section()
    faculty_eager = make_faculty(nuid=1, course_pref="Eager to teach")
    faculty_willing = make_faculty(nuid=2, course_pref="Willing to teach")
    faculty_ready = make_faculty(nuid=3, course_pref="Ready to teach")

    result = get_eligible_ranked_faculty(section, [faculty_willing, faculty_eager, faculty_ready])
    assert result == [faculty_eager, faculty_ready, faculty_willing]


# ---------------------
# Ranking: constraint count tiebreaker
# ---------------------


def test_tiebreak_by_constraint_count():
    section = make_section()
    # Both pref level 1, but faculty_a has more assigned time blocks
    faculty_a = make_faculty(nuid=1, course_pref="Eager to teach", assigned_time_blocks={20, 30})
    faculty_b = make_faculty(nuid=2, course_pref="Eager to teach", assigned_time_blocks={20})

    result = get_eligible_ranked_faculty(section, [faculty_a, faculty_b])
    assert result == [faculty_b, faculty_a]


# ---------------------
# Ranking: time preference tiebreaker
# ---------------------


def test_tiebreak_by_time_preference():
    section = make_section(time_block_id=10)
    # Same course pref, same constraint count, different time pref
    faculty_a = make_faculty(nuid=1, course_pref="Eager to teach", time_pref="Willing to teach")
    faculty_b = make_faculty(nuid=2, course_pref="Eager to teach", time_pref="Eager to teach")

    result = get_eligible_ranked_faculty(section, [faculty_a, faculty_b])
    assert result == [faculty_b, faculty_a]


# ---------------------
# Unrated time preference: included but ranks last
# ---------------------


def test_unrated_time_pref_ranks_last():
    section = make_section(time_block_id=10)

    faculty_rated = make_faculty(nuid=1, course_pref="Eager to teach", time_pref="Willing to teach")
    faculty_unrated = FacultyState(
        nuid=2,
        max_load=3,
        current_load=0,
        course_preferences=[
            CoursePreferenceInfo(
                course_id=100,
                course_name="Test Course",
                preference="Eager to teach",
            )
        ],
        time_preferences=[],  # no time pref entry
        assigned_time_blocks=set(),
    )

    result = get_eligible_ranked_faculty(section, [faculty_unrated, faculty_rated])
    assert result == [faculty_rated, faculty_unrated]


# ---------------------
# Empty inputs
# ---------------------


def test_empty_faculty_list():
    section = make_section()
    result = get_eligible_ranked_faculty(section, [])
    assert result == []


def test_all_faculty_excluded():
    section = make_section()
    faculty_a = make_faculty(nuid=1, course_pref="Not my cup of tea")
    faculty_b = make_faculty(nuid=2, max_load=1, current_load=1)
    faculty_c = make_faculty(nuid=3, assigned_time_blocks={10})

    result = get_eligible_ranked_faculty(section, [faculty_a, faculty_b, faculty_c])
    assert result == []
