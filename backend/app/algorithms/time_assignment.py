"""
1.  Sort the assignments so the faculty with the fewest rated time
    preferences go first.

2.  For each assignment, filter the full list of time blocks down to only
    the eligible ones

3.  Sort the eligible blocks by (preference rank, campus-day impact) and
    pick the first one.

4.  If no eligible block exists -> record a NO_VALID_TIME_BLOCK warning and
    leave the section unplaced
"""

import math
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from app.algorithms.models import (
    MatchedAssignment,
    SectionAssignment,
    TimeBlockAssignmentResult,
)
from app.core.enums import PreferenceLevel, Severity, WarningType
from app.schemas.algorithm_params import AlgorithmParameters
from app.schemas.section import MeetingPreferenceInfo
from app.schemas.warning import Warning


def department_code_from_course_name(course_name: str) -> str:
    # Return the subject prefix ("CS", "DS", "CY") from a course name.
    part = course_name.strip().split(maxsplit=1)[0]
    return part.upper()


def _tb_id(block: Any) -> int:
    # Pull the integer time_block_id
    return int(block.time_block_id)


def _meeting_days(block: Any) -> str:
    # Return the meeting_days string ("MWF", "TR", etc.)
    return str(block.meeting_days)


def _days_set(meeting_days: str) -> frozenset[str]:
    # Convert a days string like "MWF" into a frozenset {"M", "W", "F"}.
    return frozenset(c for c in meeting_days.strip().upper() if c.isalpha())


def _time_pref_level(prefs: Sequence[MeetingPreferenceInfo], time_block_id: int) -> int | None:
    # Returns 1–4 from PreferenceLevel, or None if unrated or preference is unrecognized.
    for p in prefs:
        if p.time_block_id == time_block_id:
            try:
                return PreferenceLevel(p.preference).to_int()
            except ValueError:
                # Malformed preference value — treat as unrated rather than aborting the run.
                return None
    return None


def _sort_key_for_block(
    time_block_id: int,
    pref_rank: int,
    faculty_day_set: frozenset[str],
    block_days: frozenset[str],
) -> tuple[int, int, int, int]:
    """Sorting critera

    1: pref_rank: Faculty's own preference rating (1 best, 4 worst).

    2: total merged campus days: How many distinct weekdays this faculty would be on campus

    3: new days only: Among blocks with the same total days, prefer the one that adds the
    fewest new days
    """
    merged = faculty_day_set | block_days  # days on campus after adding this block
    new_only = len(block_days - faculty_day_set)  # how many of those are new
    return (pref_rank, len(merged), new_only, time_block_id)


def assign_time_blocks(
    assignments: list[MatchedAssignment],
    time_blocks: Sequence[Any],
    faculty_time_preferences: Mapping[int, Sequence[MeetingPreferenceInfo]],
    *,
    parameters: AlgorithmParameters | None = None,
    existing_faculty_time_blocks: Mapping[int, Iterable[int]] | None = None,
    initial_department_time_block_counts: Mapping[tuple[str, int], int] | None = None,
    department_section_totals: Mapping[str, int] | None = None,
) -> TimeBlockAssignmentResult:

    params = parameters or AlgorithmParameters()
    cap = float(params.MaxTimeBlockCapacity)  # 0.15

    warnings: list[Warning] = []
    out: list[SectionAssignment] = []

    # set of time_block_ids already assigned to them.
    # pre-populated from existing_faculty_time_blocks for multi-batch runs.
    faculty_blocks: dict[int, set[int]] = defaultdict(set)
    if existing_faculty_time_blocks:
        for nuid, blocks in existing_faculty_time_blocks.items():
            faculty_blocks[int(nuid)].update(int(b) for b in blocks)

    # how many sections of that dept are in that block.
    dept_tb_counts: dict[tuple[str, int], int] = defaultdict(int)
    if initial_department_time_block_counts:
        for (dept, tb), c in initial_department_time_block_counts.items():
            dept_tb_counts[(dept.upper(), int(tb))] = int(c)

    # total sections in this department (used as denominator for capacity)
    dept_totals: dict[str, int] = defaultdict(int)
    for a in assignments:
        dept_totals[a.department_code.upper()] += 1
    if department_section_totals:
        for dept, n in department_section_totals.items():
            dept_totals[dept.upper()] = max(dept_totals[dept.upper()], int(n))

    def prefs_for(nuid: int) -> Sequence[MeetingPreferenceInfo]:
        # return the preference list for one faculty member
        return faculty_time_preferences.get(nuid, ())

    # faculty with fewer rated time preferences are more constrained, so
    # schedule them first.

    indexed = list(enumerate(assignments))
    indexed.sort(
        key=lambda it: (
            len(list(prefs_for(it[1].faculty_nuid))),  # fewer prefs -> earlier
            it[1].department_code,
            it[1].faculty_nuid,
            it[1].section_id,
        )
    )

    # precompute weekday sets per block (avoids re-parsing every single time)
    block_day_cache: dict[int, frozenset[str]] = {
        _tb_id(b): _days_set(_meeting_days(b)) for b in time_blocks
    }

    # assigning -> uses greedy
    for _, assign in indexed:
        nuid = assign.faculty_nuid
        dept = assign.department_code.upper()
        total_dept = dept_totals[dept]
        prefs = prefs_for(nuid)

        # which campus days this faculty already has -> using to minimize new days
        faculty_days: set[str] = set()
        for tb_id in faculty_blocks[nuid]:
            faculty_days.update(block_day_cache.get(tb_id, frozenset()))

        # Filter to eligible time blocks
        # A block is eligible when it passes both checks:
        #   - Not already held by this faculty
        #   - Adding it wouldn't push this department over the cap.

        # Each entry is (time_block_id, pref_rank). pref_rank is 1–4 or 99 if unrated
        eligible: list[tuple[int, int]] = []

        for block in time_blocks:
            tb = _tb_id(block)

            # faculty already teaches at this time -> skip
            if tb in faculty_blocks[nuid]:
                continue

            # department percentage cap
            if total_dept > 0 and total_dept * cap >= 1:
                current = dept_tb_counts[(dept, tb)]
                if (current + 1) / total_dept > cap:
                    continue  # would exceed 15 % -> skip

            # Block passed both checks -> record it with its preference rank in eligible
            pref = _time_pref_level(prefs, tb)

            # If professor chooses "not my cup of tea"
            if pref == 4:
                continue
            pref_rank = pref if pref is not None else 99  # unrated sorts last
            eligible.append((tb, pref_rank))

        # no valid block -> add to warnings
        if not eligible:
            warnings.append(
                Warning(
                    Type=WarningType.NO_VALID_TIME_BLOCK,
                    SeverityRank=Severity.MEDIUM,
                    # returned message
                    Message=(
                        f"No time block available for section {assign.section_id} "
                        f"(course {assign.course_id}, faculty {nuid}, dept {dept}). "
                    ),
                    FacultyID=nuid,
                    CourseID=assign.course_id,
                    BlockID=None,
                )
            )
            # return all the SectionAssignments we have so far
            # plus the ones with time_block_id=None to indicate unplaced
            out.append(
                SectionAssignment(
                    section_id=assign.section_id,
                    faculty_nuid=nuid,
                    time_block_id=None,
                    time_preference_level=None,
                )
            )
            continue

        # Pick the best eligible block
        # Sort ascending, the first element is the chosen one
        faculty_day_frozen = frozenset(faculty_days)
        eligible.sort(
            key=lambda row: _sort_key_for_block(
                row[0], row[1], faculty_day_frozen, block_day_cache[row[0]]
            )
        )
        best_tb, pref_rank = eligible[0]
        pref_stored = None if pref_rank == 99 else pref_rank

        # Record this assignment in our outputs
        faculty_blocks[nuid].add(best_tb)  # mark this slot as taken for this faculty
        dept_tb_counts[(dept, best_tb)] += 1  # increment dept-block counter

        out.append(
            SectionAssignment(
                section_id=assign.section_id,
                faculty_nuid=nuid,
                time_block_id=best_tb,
                time_preference_level=pref_stored,
            )
        )

    # Final sort by section_id for display
    out.sort(key=lambda s: s.section_id)
    return TimeBlockAssignmentResult(assignments=out, warnings=warnings)


# The following function is the exact same department cap logic used in assign_time_blocks
# used so the UI can call it to show it without running the full algorithm.


def max_sections_per_block_for_department(
    department_section_count: int,
    parameters: AlgorithmParameters | None = None,
) -> int:
    # Return the max sections of one department allowed in a single time block.
    # if the department is tiny, the cap doesn't apply and we return the full count.
    params = parameters or AlgorithmParameters()
    n = department_section_count
    if n <= 0:
        return 0
    cap = float(params.MaxTimeBlockCapacity)
    if n * cap < 1:
        return n
    return math.floor(n * cap)
