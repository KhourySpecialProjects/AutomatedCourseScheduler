"""Tests for app/algorithms/matching.py

SSIP-93: get_eligible_ranked_faculty
SSIP-91: matching loop + displacement logic + output construction
"""

from collections import Counter

from app.algorithms.matching import (
    _assign_section,
    _build_output,
    _build_pref_lookup,
    _expand_sections,
    _find_displacement_target,
    _unassign_section,
    get_eligible_ranked_faculty,
    match_courses_to_faculty,
)
from app.algorithms.models import FacultyState, SectionCandidate
from app.schemas.algorithm_input import AlgorithmInput
from app.schemas.course import CourseResponse
from app.schemas.faculty import FacultyProfileResponse
from app.schemas.section import CoursePreferenceInfo, MeetingPreferenceInfo

# ---------------------
# Helpers
# ---------------------

EAGER = "Eager to teach"
READY = "Ready to teach"
WILLING = "Willing to teach"
NOT_INTERESTED = "Not my cup of tea"


def make_section(
    section_id: int = 1,
    course_id: int = 100,
    time_block_id: int = 10,
    is_priority: bool = False,
    seen_second_pass: bool = False,
) -> SectionCandidate:
    return SectionCandidate(
        section_id=section_id,
        course_id=course_id,
        time_block_id=time_block_id,
        is_priority=is_priority,
        seen_second_pass=seen_second_pass,
    )


def make_faculty(
    nuid: int = 1,
    max_load: int = 3,
    current_load: int = 0,
    course_id: int = 100,
    course_pref: str = EAGER,
    time_block_id: int = 10,
    time_pref: str = EAGER,
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


def make_faculty_multi(
    nuid: int = 1,
    max_load: int = 3,
    current_load: int = 0,
    course_prefs: list[tuple[int, str]] | None = None,
    time_prefs: list[tuple[int, str]] | None = None,
    assigned_time_blocks: set[int] | None = None,
) -> FacultyState:
    """Build FacultyState with multiple course/time preferences.

    course_prefs: list of (course_id, preference_str)
    time_prefs:   list of (time_block_id, preference_str)
    """
    cps = [
        CoursePreferenceInfo(course_id=cid, course_name=f"Course {cid}", preference=p)
        for cid, p in (course_prefs or [])
    ]
    tps = [MeetingPreferenceInfo(time_block_id=tid, preference=p) for tid, p in (time_prefs or [])]
    return FacultyState(
        nuid=nuid,
        max_load=max_load,
        current_load=current_load,
        course_preferences=cps,
        time_preferences=tps,
        assigned_time_blocks=assigned_time_blocks or set(),
    )


def make_course_response(
    course_id: int = 100,
    section_count: int = 1,
    priority: bool = False,
    qualified_faculty: int = 5,
) -> CourseResponse:
    return CourseResponse(
        CourseID=course_id,
        CourseNo=1000,
        CourseName=f"Course {course_id}",
        CourseDescription="desc",
        SectionCount=section_count,
        Priority=priority,
        QualifiedFaculty=qualified_faculty,
    )


def make_faculty_profile(
    nuid: int = 1,
    max_load: int = 3,
    course_prefs: list[tuple[int, str]] | None = None,
    meeting_prefs: list[tuple[int, str]] | None = None,
) -> FacultyProfileResponse:
    cps = [
        CoursePreferenceInfo(course_id=cid, course_name=f"Course {cid}", preference=p)
        for cid, p in (course_prefs or [])
    ]
    mps = [
        MeetingPreferenceInfo(time_block_id=tid, preference=p) for tid, p in (meeting_prefs or [])
    ]
    return FacultyProfileResponse(
        nuid=nuid,
        first_name="Faculty",
        last_name=f"#{nuid}",
        email=f"f{nuid}@example.com",
        title="Professor",
        campus=1,
        active=True,
        maxLoad=max_load,
        course_preferences=cps,
        meeting_preferences=mps,
    )


def make_algorithm_input(
    courses: list[CourseResponse] | None = None,
    faculty: list[FacultyProfileResponse] | None = None,
) -> tuple[list[SectionCandidate], AlgorithmInput]:
    courses = courses or []
    return _expand_sections(courses), AlgorithmInput(
        OfferedCourses=courses,
        AllFaculty=faculty or [],
        TimeBlocks=[],
    )


# ===========================================================================
# SSIP-93: get_eligible_ranked_faculty
# ===========================================================================

# ---------------------
# Hard exclude: NOT_INTERESTED
# ---------------------


def test_not_interested_is_excluded():
    section = make_section()
    faculty = make_faculty(course_pref=NOT_INTERESTED)
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
                course_id=999,
                course_name="Other Course",
                preference=EAGER,
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
    faculty_eager = make_faculty(nuid=1, course_pref=EAGER)
    faculty_willing = make_faculty(nuid=2, course_pref=WILLING)
    faculty_ready = make_faculty(nuid=3, course_pref=READY)

    result = get_eligible_ranked_faculty(section, [faculty_willing, faculty_eager, faculty_ready])
    assert result == [faculty_eager, faculty_ready, faculty_willing]


# ---------------------
# Ranking: constraint count tiebreaker
# ---------------------


def test_tiebreak_by_constraint_count():
    section = make_section()
    faculty_a = make_faculty(nuid=1, course_pref=EAGER, assigned_time_blocks={20, 30})
    faculty_b = make_faculty(nuid=2, course_pref=EAGER, assigned_time_blocks={20})

    result = get_eligible_ranked_faculty(section, [faculty_a, faculty_b])
    assert result == [faculty_b, faculty_a]


# ---------------------
# Ranking: time preference tiebreaker
# ---------------------


def test_tiebreak_by_time_preference():
    section = make_section(time_block_id=10)
    faculty_a = make_faculty(nuid=1, course_pref=EAGER, time_pref=WILLING)
    faculty_b = make_faculty(nuid=2, course_pref=EAGER, time_pref=EAGER)

    result = get_eligible_ranked_faculty(section, [faculty_a, faculty_b])
    assert result == [faculty_b, faculty_a]


# ---------------------
# Unrated time preference: included but ranks last
# ---------------------


def test_unrated_time_pref_ranks_last():
    section = make_section(time_block_id=10)

    faculty_rated = make_faculty(nuid=1, course_pref=EAGER, time_pref=WILLING)
    faculty_unrated = FacultyState(
        nuid=2,
        max_load=3,
        current_load=0,
        course_preferences=[
            CoursePreferenceInfo(
                course_id=100,
                course_name="Test Course",
                preference=EAGER,
            )
        ],
        time_preferences=[],
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
    faculty_a = make_faculty(nuid=1, course_pref=NOT_INTERESTED)
    faculty_b = make_faculty(nuid=2, max_load=1, current_load=1)
    faculty_c = make_faculty(nuid=3, assigned_time_blocks={10})

    result = get_eligible_ranked_faculty(section, [faculty_a, faculty_b, faculty_c])
    assert result == []


# ===========================================================================
# SSIP-91: _expand_sections
# ===========================================================================


class TestExpandSections:
    def test_single_course_single_section(self):
        courses = [make_course_response(course_id=10, section_count=1, priority=True)]
        sections = _expand_sections(courses)
        assert len(sections) == 1
        assert sections[0].course_id == 10
        assert sections[0].section_id == 0
        assert sections[0].is_priority is True
        assert sections[0].time_block_id is None

    def test_single_course_multiple_sections(self):
        courses = [make_course_response(course_id=10, section_count=3)]
        sections = _expand_sections(courses)
        assert len(sections) == 3
        assert [s.section_id for s in sections] == [0, 1, 2]
        assert all(s.course_id == 10 for s in sections)

    def test_multiple_courses(self):
        courses = [
            make_course_response(course_id=10, section_count=2, priority=True),
            make_course_response(course_id=20, section_count=1, priority=False),
        ]
        sections = _expand_sections(courses)
        assert len(sections) == 3
        assert [s.section_id for s in sections] == [0, 1, 2]
        assert sections[0].course_id == 10
        assert sections[2].course_id == 20

    def test_zero_section_count(self):
        courses = [make_course_response(course_id=10, section_count=0)]
        assert _expand_sections(courses) == []

    def test_empty_courses(self):
        assert _expand_sections([]) == []


# ===========================================================================
# SSIP-91: _build_pref_lookup
# ===========================================================================


class TestBuildPrefLookup:
    def test_basic_lookup(self):
        faculty = [
            make_faculty_multi(nuid=1, course_prefs=[(100, EAGER), (200, WILLING)]),
            make_faculty_multi(nuid=2, course_prefs=[(100, NOT_INTERESTED)]),
        ]
        lookup = _build_pref_lookup(faculty)
        assert lookup[1][100] == 1
        assert lookup[1][200] == 3
        assert lookup[2][100] == 4

    def test_empty_faculty(self):
        assert _build_pref_lookup([]) == {}

    def test_faculty_with_no_prefs(self):
        faculty = [make_faculty_multi(nuid=1, course_prefs=[])]
        lookup = _build_pref_lookup(faculty)
        assert lookup[1] == {}


# ===========================================================================
# SSIP-91: _assign_section / _unassign_section
# ===========================================================================


class TestAssignUnassign:
    def test_assign_updates_all_state(self):
        section = make_section(section_id=0, course_id=100, time_block_id=10)
        faculty = make_faculty(nuid=1, max_load=3, current_load=0)
        assignments = {}

        _assign_section(section, faculty, 1, assignments)

        assert section.assigned_faculty_nuid == 1
        assert section.assigned_pref_level == 1
        assert faculty.current_load == 1
        assert 10 in faculty.assigned_time_blocks
        assert assignments[0] == (1, 1)

    def test_assign_no_time_block(self):
        section = make_section(section_id=0, time_block_id=None)
        faculty = make_faculty(nuid=1)
        assignments = {}

        _assign_section(section, faculty, 2, assignments)

        assert faculty.current_load == 1
        assert faculty.assigned_time_blocks == set()
        assert assignments[0] == (1, 2)

    def test_unassign_reverts_state(self):
        section = make_section(section_id=0, time_block_id=10)
        faculty = make_faculty(nuid=1, current_load=1, assigned_time_blocks={10})
        section.assigned_faculty_nuid = 1
        section.assigned_pref_level = 1
        assignments = {0: (1, 1)}

        _unassign_section(section, faculty, assignments)

        assert section.assigned_faculty_nuid is None
        assert section.assigned_pref_level is None
        assert faculty.current_load == 0
        assert 10 not in faculty.assigned_time_blocks
        assert 0 not in assignments

    def test_unassign_no_time_block(self):
        section = make_section(section_id=0, time_block_id=None)
        faculty = make_faculty(nuid=1, current_load=1)
        section.assigned_faculty_nuid = 1
        assignments = {0: (1, 1)}

        _unassign_section(section, faculty, assignments)

        assert faculty.current_load == 0
        assert 0 not in assignments


# ===========================================================================
# SSIP-91: _find_displacement_target
# ===========================================================================


class TestFindDisplacementTarget:
    def _setup(self, sections, faculty_list):
        faculty_states = {f.nuid: f for f in faculty_list}
        section_lookup = {s.section_id: s for s in sections}
        pref_lookup = _build_pref_lookup(faculty_list)
        return faculty_states, section_lookup, pref_lookup

    def test_cross_tier_displacement(self):
        """Priority section displaces non-priority assignment."""
        faculty = make_faculty_multi(
            nuid=1,
            max_load=1,
            current_load=1,
            course_prefs=[(100, EAGER), (200, WILLING)],
        )
        existing = make_section(section_id=0, course_id=200, is_priority=False)
        incoming = make_section(section_id=1, course_id=100, is_priority=True)

        assignments = {0: (1, 3)}
        faculty_states, section_lookup, pref_lookup = self._setup([existing, incoming], [faculty])
        result = _find_displacement_target(
            incoming, faculty_states, assignments, section_lookup, pref_lookup
        )
        assert result == (0, 1)

    def test_within_tier_strict_improvement(self):
        """Same priority: displacement only if incoming has better pref."""
        faculty = make_faculty_multi(
            nuid=1,
            max_load=1,
            current_load=1,
            course_prefs=[(100, EAGER), (200, WILLING)],
        )
        existing = make_section(section_id=0, course_id=200, is_priority=False)
        incoming = make_section(section_id=1, course_id=100, is_priority=False)

        assignments = {0: (1, 3)}
        faculty_states, section_lookup, pref_lookup = self._setup([existing, incoming], [faculty])
        result = _find_displacement_target(
            incoming, faculty_states, assignments, section_lookup, pref_lookup
        )
        assert result == (0, 1)

    def test_within_tier_no_improvement_blocked(self):
        """Same priority, no improvement: displacement denied."""
        faculty = make_faculty_multi(
            nuid=1,
            max_load=1,
            current_load=1,
            course_prefs=[(100, WILLING), (200, EAGER)],
        )
        existing = make_section(section_id=0, course_id=200, is_priority=False)
        incoming = make_section(section_id=1, course_id=100, is_priority=False)

        assignments = {0: (1, 1)}
        faculty_states, section_lookup, pref_lookup = self._setup([existing, incoming], [faculty])
        result = _find_displacement_target(
            incoming, faculty_states, assignments, section_lookup, pref_lookup
        )
        assert result is None

    def test_must_have_protection(self):
        """Cannot displace a priority section when MUST_HAVE_PROTECTION is True."""
        faculty = make_faculty_multi(
            nuid=1,
            max_load=1,
            current_load=1,
            course_prefs=[(100, EAGER), (200, WILLING)],
        )
        existing = make_section(section_id=0, course_id=200, is_priority=True)
        incoming = make_section(section_id=1, course_id=100, is_priority=True)

        assignments = {0: (1, 3)}
        faculty_states, section_lookup, pref_lookup = self._setup([existing, incoming], [faculty])
        result = _find_displacement_target(
            incoming, faculty_states, assignments, section_lookup, pref_lookup
        )
        assert result is None

    def test_seen_second_pass_blocks_cascade(self):
        """Cannot displace a section already displaced once."""
        faculty = make_faculty_multi(
            nuid=1,
            max_load=1,
            current_load=1,
            course_prefs=[(100, EAGER), (200, WILLING)],
        )
        existing = make_section(
            section_id=0, course_id=200, is_priority=False, seen_second_pass=True
        )
        incoming = make_section(section_id=1, course_id=100, is_priority=True)

        assignments = {0: (1, 3)}
        faculty_states, section_lookup, pref_lookup = self._setup([existing, incoming], [faculty])
        result = _find_displacement_target(
            incoming, faculty_states, assignments, section_lookup, pref_lookup
        )
        assert result is None

    def test_faculty_not_at_capacity_skipped(self):
        """Faculty with remaining capacity are skipped."""
        faculty = make_faculty_multi(
            nuid=1,
            max_load=2,
            current_load=1,
            course_prefs=[(100, EAGER), (200, WILLING)],
        )
        existing = make_section(section_id=0, course_id=200, is_priority=False)
        incoming = make_section(section_id=1, course_id=100, is_priority=True)

        assignments = {0: (1, 3)}
        faculty_states, section_lookup, pref_lookup = self._setup([existing, incoming], [faculty])
        result = _find_displacement_target(
            incoming, faculty_states, assignments, section_lookup, pref_lookup
        )
        assert result is None

    def test_unqualified_faculty_skipped(self):
        """Faculty with NOT_INTERESTED for incoming course are skipped."""
        faculty = make_faculty_multi(
            nuid=1,
            max_load=1,
            current_load=1,
            course_prefs=[(100, NOT_INTERESTED), (200, EAGER)],
        )
        existing = make_section(section_id=0, course_id=200, is_priority=False)
        incoming = make_section(section_id=1, course_id=100, is_priority=True)

        assignments = {0: (1, 1)}
        faculty_states, section_lookup, pref_lookup = self._setup([existing, incoming], [faculty])
        result = _find_displacement_target(
            incoming, faculty_states, assignments, section_lookup, pref_lookup
        )
        assert result is None

    def test_no_assignments_returns_none(self):
        faculty = make_faculty_multi(
            nuid=1, max_load=1, current_load=1, course_prefs=[(100, EAGER)]
        )
        incoming = make_section(section_id=0, course_id=100)

        result = _find_displacement_target(
            incoming, {1: faculty}, {}, {}, _build_pref_lookup([faculty])
        )
        assert result is None


# ===========================================================================
# SSIP-91: _build_output
# ===========================================================================


class TestBuildOutput:
    def test_matched_sections(self):
        sections = [make_section(section_id=0, course_id=100)]
        assignments = {0: (1, 1)}
        pref_lookup = {1: {100: 1}}

        output = _build_output(sections, assignments, [], pref_lookup)

        assert len(output) == 1
        assert output[0].is_matched is True
        assert output[0].faculty_nuid == 1
        assert output[0].assigned_pref_level == 1
        assert output[0].unmatched_reason is None

    def test_unmatched_no_qualified_faculty(self):
        sections = [make_section(section_id=0, course_id=100)]
        pref_lookup = {1: {100: 4}}

        output = _build_output(sections, {}, [sections[0]], pref_lookup)

        assert output[0].is_matched is False
        assert output[0].unmatched_reason == "no_qualified_faculty"

    def test_unmatched_insufficient_supply(self):
        sections = [make_section(section_id=0, course_id=100)]
        pref_lookup = {1: {100: 1}}

        output = _build_output(sections, {}, [sections[0]], pref_lookup)

        assert output[0].is_matched is False
        assert output[0].unmatched_reason == "insufficient_supply"

    def test_empty_pref_lookup(self):
        sections = [make_section(section_id=0, course_id=100)]
        output = _build_output(sections, {}, [sections[0]], {})
        assert output[0].unmatched_reason == "no_qualified_faculty"


# ===========================================================================
# SSIP-91: match_courses_to_faculty (integration)
# ===========================================================================


class TestMatchCoursesToFaculty:
    def test_simple_assignment(self):
        """Two faculty, two sections — both matched to best-preference faculty."""
        courses = [
            make_course_response(course_id=100, section_count=1),
            make_course_response(course_id=200, section_count=1),
        ]
        faculty = [
            make_faculty_profile(nuid=1, course_prefs=[(100, EAGER), (200, WILLING)]),
            make_faculty_profile(nuid=2, course_prefs=[(100, WILLING), (200, EAGER)]),
        ]
        sections, input = make_algorithm_input(courses, faculty)
        result = match_courses_to_faculty(sections, input)

        assert len(result) == 2
        assert all(a.is_matched for a in result)

        by_course = {a.course_id: a for a in result}
        assert by_course[100].faculty_nuid == 1
        assert by_course[100].assigned_pref_level == 1
        assert by_course[200].faculty_nuid == 2
        assert by_course[200].assigned_pref_level == 1

    def test_priority_displaces_non_priority(self):
        """Priority section takes faculty from non-priority when no other option."""
        courses = [
            make_course_response(course_id=200, section_count=1, priority=False),
            make_course_response(course_id=100, section_count=1, priority=True),
        ]
        faculty = [
            make_faculty_profile(
                nuid=1,
                max_load=1,
                course_prefs=[(100, EAGER), (200, WILLING)],
            ),
        ]
        sections, input = make_algorithm_input(courses, faculty)
        result = match_courses_to_faculty(sections, input)

        matched = [a for a in result if a.is_matched]
        unmatched = [a for a in result if not a.is_matched]

        assert len(matched) == 1
        assert matched[0].course_id == 100
        assert matched[0].faculty_nuid == 1
        assert len(unmatched) == 1
        assert unmatched[0].course_id == 200

    def test_no_qualified_faculty_all_unmatched(self):
        courses = [make_course_response(course_id=100, section_count=2)]
        faculty = [
            make_faculty_profile(nuid=1, course_prefs=[(100, NOT_INTERESTED)]),
            make_faculty_profile(nuid=2, course_prefs=[(100, NOT_INTERESTED)]),
        ]
        sections, input = make_algorithm_input(courses, faculty)
        result = match_courses_to_faculty(sections, input)

        assert len(result) == 2
        assert all(not a.is_matched for a in result)
        assert all(a.unmatched_reason == "no_qualified_faculty" for a in result)

    def test_insufficient_supply(self):
        """Qualified faculty exist but all at capacity, no displacement possible."""
        courses = [
            make_course_response(course_id=100, section_count=1),
            make_course_response(course_id=200, section_count=1),
            make_course_response(course_id=300, section_count=1),
        ]
        faculty = [
            make_faculty_profile(
                nuid=1,
                max_load=2,
                course_prefs=[(100, EAGER), (200, EAGER), (300, EAGER)],
            ),
        ]
        sections, input = make_algorithm_input(courses, faculty)
        result = match_courses_to_faculty(sections, input)

        matched = [a for a in result if a.is_matched]
        unmatched = [a for a in result if not a.is_matched]

        assert len(matched) == 2
        assert len(unmatched) == 1
        assert unmatched[0].unmatched_reason == "insufficient_supply"

    def test_second_pass_termination(self):
        """Displaced section fails second time — terminates, doesn't loop forever."""
        courses = [
            make_course_response(course_id=100, section_count=1, priority=True),
            make_course_response(course_id=200, section_count=1, priority=False),
        ]
        faculty = [
            make_faculty_profile(
                nuid=1,
                max_load=1,
                course_prefs=[(100, EAGER), (200, WILLING)],
            ),
        ]
        sections, input = make_algorithm_input(courses, faculty)
        result = match_courses_to_faculty(sections, input)

        assert len(result) == 2
        matched = [a for a in result if a.is_matched]
        assert len(matched) == 1

    def test_empty_courses_returns_empty(self):
        sections, input = make_algorithm_input([], [])
        result = match_courses_to_faculty(sections, input)
        assert result == []

    def test_empty_faculty_all_unmatched(self):
        courses = [make_course_response(course_id=100, section_count=2)]
        sections, input = make_algorithm_input(courses, [])
        result = match_courses_to_faculty(sections, input)

        assert len(result) == 2
        assert all(not a.is_matched for a in result)
        assert all(a.unmatched_reason == "no_qualified_faculty" for a in result)

    def test_within_tier_displacement_strict_improvement(self):
        """Non-priority displaces another non-priority only on strict pref improvement."""
        courses = [
            make_course_response(course_id=200, section_count=1, priority=False),
            make_course_response(course_id=100, section_count=1, priority=False),
        ]
        faculty = [
            make_faculty_profile(
                nuid=1,
                max_load=1,
                course_prefs=[(100, EAGER), (200, WILLING)],
            ),
        ]
        sections, input = make_algorithm_input(courses, faculty)
        result = match_courses_to_faculty(sections, input)

        matched = [a for a in result if a.is_matched]
        assert len(matched) == 1
        assert matched[0].course_id == 100
        assert matched[0].assigned_pref_level == 1

    def test_must_have_protection_prevents_displacement(self):
        """Priority section already matched cannot be displaced by another priority."""
        courses = [
            make_course_response(course_id=100, section_count=1, priority=True),
            make_course_response(course_id=200, section_count=1, priority=True),
        ]
        faculty = [
            make_faculty_profile(
                nuid=1,
                max_load=1,
                course_prefs=[(100, WILLING), (200, EAGER)],
            ),
        ]
        sections, input = make_algorithm_input(courses, faculty)
        result = match_courses_to_faculty(sections, input)

        matched = [a for a in result if a.is_matched]
        unmatched = [a for a in result if not a.is_matched]

        assert len(matched) == 1
        assert len(unmatched) == 1

    def test_multiple_faculty_best_preference_wins(self):
        courses = [make_course_response(course_id=100, section_count=1)]
        faculty = [
            make_faculty_profile(nuid=1, course_prefs=[(100, WILLING)]),
            make_faculty_profile(nuid=2, course_prefs=[(100, EAGER)]),
            make_faculty_profile(nuid=3, course_prefs=[(100, READY)]),
        ]
        sections, input = make_algorithm_input(courses, faculty)
        result = match_courses_to_faculty(sections, input)

        assert len(result) == 1
        assert result[0].is_matched is True
        assert result[0].faculty_nuid == 2
        assert result[0].assigned_pref_level == 1

    def test_many_sections_many_faculty(self):
        """3 courses × 2 sections = 6 sections, 4 faculty with max_load=2."""
        courses = [
            make_course_response(course_id=100, section_count=2, priority=True),
            make_course_response(course_id=200, section_count=2),
            make_course_response(course_id=300, section_count=2),
        ]
        faculty = [
            make_faculty_profile(
                nuid=1,
                max_load=2,
                course_prefs=[(100, EAGER), (200, READY), (300, WILLING)],
            ),
            make_faculty_profile(
                nuid=2,
                max_load=2,
                course_prefs=[(100, READY), (200, EAGER), (300, READY)],
            ),
            make_faculty_profile(
                nuid=3,
                max_load=2,
                course_prefs=[(100, WILLING), (200, WILLING), (300, EAGER)],
            ),
            make_faculty_profile(
                nuid=4,
                max_load=2,
                course_prefs=[(100, WILLING), (200, READY), (300, READY)],
            ),
        ]
        sections, input = make_algorithm_input(courses, faculty)
        result = match_courses_to_faculty(sections, input)

        assert len(result) == 6
        assert all(a.is_matched for a in result)

        faculty_counts = Counter(a.faculty_nuid for a in result if a.is_matched)
        assert all(count <= 2 for count in faculty_counts.values())

    def test_not_interested_hard_excluded(self):
        courses = [make_course_response(course_id=100, section_count=1)]
        faculty = [
            make_faculty_profile(nuid=1, course_prefs=[(100, NOT_INTERESTED)]),
            make_faculty_profile(nuid=2, course_prefs=[(100, EAGER)]),
        ]
        sections, input = make_algorithm_input(courses, faculty)
        result = match_courses_to_faculty(sections, input)
        assert result[0].faculty_nuid == 2

    def test_faculty_capacity_respected(self):
        courses = [
            make_course_response(course_id=100, section_count=1),
            make_course_response(course_id=200, section_count=1),
            make_course_response(course_id=300, section_count=1),
        ]
        faculty = [
            make_faculty_profile(
                nuid=1,
                max_load=1,
                course_prefs=[(100, EAGER), (200, EAGER), (300, EAGER)],
            ),
            make_faculty_profile(
                nuid=2,
                max_load=1,
                course_prefs=[(100, EAGER), (200, EAGER), (300, EAGER)],
            ),
        ]
        sections, input = make_algorithm_input(courses, faculty)
        result = match_courses_to_faculty(sections, input)

        matched = [a for a in result if a.is_matched]
        unmatched = [a for a in result if not a.is_matched]

        assert len(matched) == 2
        assert len(unmatched) == 1
