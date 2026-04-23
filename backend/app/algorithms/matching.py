from collections import deque

from app.algorithms.models import CourseAssignment, FacultyState, SectionCandidate
from app.core.enums import PreferenceLevel
from app.schemas.algorithm_input import AlgorithmInput
from app.schemas.course import CourseResponse
from app.schemas.faculty import FacultyProfileResponse


def get_eligible_ranked_faculty(
    section: SectionCandidate,
    all_faculty: list[FacultyState],
) -> list[FacultyState]:
    """Returns faculty eligible to teach the given section, ranked by
    course preference -> constraint count -> time preference."""
    eligible = []

    for faculty in all_faculty:
        # 1. Time block conflict check
        if section.time_block_id in faculty.assigned_time_blocks:
            continue

        # 2. Capacity check
        if faculty.current_load >= faculty.max_load:
            continue

        # 3. Find course preference
        pref_int = None
        for pref in faculty.course_preferences:
            if pref.course_id == section.course_id:
                pref_int = PreferenceLevel(pref.preference).to_int()
                break

        # Unrated = not auto-assignable
        if pref_int is None:
            continue

        # Hard exclude: NOT_INTERESTED
        if pref_int == PreferenceLevel.NOT_INTERESTED.to_int():
            continue

        # 4.  Find time preference (unrated = inf, NOT_INTERESTED = hard exclude)
        time_pref_int = float("inf")
        for time_pref in faculty.time_preferences:
            if time_pref.time_block_id == section.time_block_id:
                time_pref_int = PreferenceLevel(time_pref.preference).to_int()
                break

        if time_pref_int == PreferenceLevel.NOT_INTERESTED.to_int():
            continue

        eligible.append((faculty, pref_int, time_pref_int))

    # Sort by: course pref -> constraint count -> time pref
    return [
        f
        for f, _, __ in sorted(
            eligible,
            key=lambda x: (x[1], len(x[0].assigned_time_blocks), x[2]),
        )
    ]


def _expand_sections(courses: list[CourseResponse]) -> list[SectionCandidate]:
    sections = []
    section_id = 0
    for course in courses:
        for _ in range(course.section_count):
            sections.append(
                SectionCandidate(
                    course_id=course.course_id,
                    section_id=section_id,
                    is_priority=course.priority,
                )
            )
            section_id += 1
    return sections


def _get_department_code(course_name: str) -> str:
    return course_name.strip().split(maxsplit=1)[0].upper() if course_name else ""


def _build_pref_lookup(all_faculty: list[FacultyState]) -> dict[int, dict[int, int]]:
    """Builds a lookup of faculty NUID -> course ID -> preference level."""
    lookup = {}
    for faculty in all_faculty:
        course_pref_dict = {pref.course_id: PreferenceLevel(pref.preference).to_int() for pref in faculty.course_preferences}
        lookup[faculty.nuid] = course_pref_dict
    return lookup


def _build_faculty_states(
    faculty_profiles: list[FacultyProfileResponse],
) -> dict[int, FacultyState]:
    """Converts list of FacultyProfileResponse to dict of NUID -> FacultyState."""
    faculty_states = {}
    for profile in faculty_profiles:
        faculty_states[profile.nuid] = FacultyState(
            nuid=profile.nuid,
            max_load=profile.maxLoad or 3,
            course_preferences=profile.course_preferences,
            time_preferences=profile.meeting_preferences,
        )
    return faculty_states


def _assign_section(
    section: SectionCandidate,
    faculty: FacultyState,
    pref_level: int,
    assignments: dict[int, tuple[int, int]],  # section_id -> (faculty_nuid, pref_level)
):
    section.assigned_faculty_nuid = faculty.nuid
    section.assigned_pref_level = pref_level
    faculty.current_load += 1
    if section.time_block_id is not None:
        faculty.assigned_time_blocks.add(section.time_block_id)
    assignments[section.section_id] = (faculty.nuid, pref_level)


def _unassign_section(
    section: SectionCandidate,
    faculty: FacultyState,
    assignments: dict[int, tuple[int, int]],
):
    section.assigned_faculty_nuid = None
    section.assigned_pref_level = None
    faculty.current_load -= 1
    if section.time_block_id is not None:
        faculty.assigned_time_blocks.discard(section.time_block_id)
    del assignments[section.section_id]


MUST_HAVE_PROTECTION = True


def _find_displacement_target(
    section: SectionCandidate,
    faculty_states: dict[int, FacultyState],
    assignments: dict[int, tuple[int, int]],
    section_lookup: dict[int, SectionCandidate],
    pref_lookup: dict[int, dict[int, int]],
) -> tuple[int, int] | None:
    """Returns (displaced_section_id, faculty_nuid) or None."""

    for nuid, faculty in faculty_states.items():
        # Does this faculty even want to teach the incoming section?
        incoming_rank = pref_lookup.get(nuid, {}).get(section.course_id)
        if incoming_rank is None or incoming_rank >= 4:
            continue  # not qualified

        # Time conflict with incoming section?
        if section.time_block_id is not None and section.time_block_id in faculty.assigned_time_blocks:
            continue

        # Faculty must be at capacity (otherwise get_eligible would have found them)
        if faculty.current_load < faculty.max_load:
            continue

        # Check each of their current assignments
        for assigned_sid, (assigned_nuid, assigned_pref) in assignments.items():
            if assigned_nuid != nuid:
                continue

            assigned_section = section_lookup[assigned_sid]

            # Can't cascade — already displaced once
            if assigned_section.seen_second_pass:
                continue

            # Must-have protection
            if MUST_HAVE_PROTECTION and assigned_section.is_priority:
                continue

            # Cross-tier: priority always displaces non-priority
            if section.is_priority and not assigned_section.is_priority:
                return (assigned_sid, nuid)

            # Within-tier: strict preference improvement only
            if section.is_priority == assigned_section.is_priority:
                if incoming_rank < assigned_pref:
                    return (assigned_sid, nuid)

    return None


def _build_output(
    sections: list[SectionCandidate],
    assignments: dict[int, tuple[int, int]],
    unmatched: list[SectionCandidate],
    pref_lookup: dict[int, dict[int, int]],
    course_lookup: dict[int, str] | None = None,  # course_id -> course_name
) -> list[CourseAssignment]:
    course_lookup = course_lookup or {}
    output = []
    for section in sections:
        dept = _get_department_code(course_lookup.get(section.course_id, ""))
        if section.section_id in assignments:
            nuid, pref = assignments[section.section_id]
            output.append(
                CourseAssignment(
                    section_id=section.section_id,
                    course_id=section.course_id,
                    department_code=dept,
                    faculty_nuid=nuid,
                    assigned_pref_level=pref,
                    is_matched=True,
                )
            )
        else:
            has_qualified = any(prefs.get(section.course_id, 4) <= 3 for prefs in pref_lookup.values())
            reason = "insufficient_supply" if has_qualified else "no_qualified_faculty"
            output.append(
                CourseAssignment(
                    section_id=section.section_id,
                    course_id=section.course_id,
                    department_code=dept,
                    is_matched=False,
                    unmatched_reason=reason,
                )
            )
    return output


def match_courses_to_faculty(
    sections: list[SectionCandidate],
    input: AlgorithmInput,
) -> list[CourseAssignment]:
    # 1. Build working data structures
    faculty_states = _build_faculty_states(input.AllFaculty)
    pref_lookup = _build_pref_lookup(list(faculty_states.values()))
    section_lookup = {s.section_id: s for s in sections}
    assignments: dict[int, tuple[int, int]] = {}  # section_id -> (nuid, pref)
    unmatched: list[SectionCandidate] = []

    # 2. Single queue-based loop
    queue = deque(sections)

    while queue:
        section = queue.popleft()

        # Try direct assignment
        eligible = get_eligible_ranked_faculty(section, list(faculty_states.values()))

        if eligible:
            best = eligible[0]
            pref = pref_lookup[best.nuid][section.course_id]
            _assign_section(section, best, pref, assignments)
            continue

        # No eligible faculty — try displacement
        if section.seen_second_pass:
            unmatched.append(section)
            continue

        target = _find_displacement_target(section, faculty_states, assignments, section_lookup, pref_lookup)

        if target:
            displaced_sid, nuid = target
            displaced_section = section_lookup[displaced_sid]
            faculty = faculty_states[nuid]

            _unassign_section(displaced_section, faculty, assignments)
            pref = pref_lookup[nuid][section.course_id]
            _assign_section(section, faculty, pref, assignments)

            displaced_section.seen_second_pass = True
            queue.append(displaced_section)
        else:
            unmatched.append(section)

    # 3. Build output
    course_name_lookup = {c.course_id: c.subject or "" for c in input.OfferedCourses}
    return _build_output(sections, assignments, unmatched, pref_lookup, course_name_lookup)
