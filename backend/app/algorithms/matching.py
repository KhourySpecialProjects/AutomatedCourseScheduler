from app.algorithms.models import FacultyState, SectionCandidate
from app.core.enums import PreferenceLevel


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
        if pref_int == 4:
            continue

        # 4. Find time preference (unrated = inf, not a hard exclude)
        time_pref_int = float("inf")
        for time_pref in faculty.time_preferences:
            if time_pref.time_block_id == section.time_block_id:
                time_pref_int = PreferenceLevel(time_pref.preference).to_int()
                break

        eligible.append((faculty, pref_int, time_pref_int))

    # Sort by: course pref -> constraint count -> time pref
    return [
        f
        for f, _, __ in sorted(
            eligible,
            key=lambda x: (x[1], len(x[0].assigned_time_blocks), x[2]),
        )
    ]
