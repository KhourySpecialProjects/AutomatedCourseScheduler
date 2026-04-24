"""Algorithm service — runs as background task with own DB session."""

import logging
from collections import defaultdict
from datetime import UTC, datetime

from app.algorithms.matching import _expand_sections, match_courses_to_faculty
from app.algorithms.models import MatchedAssignment
from app.algorithms.time_assignment import assign_time_blocks
from app.core.database import SessionLocal
from app.core.enums import ScheduleStatus, WarningType
from app.models.faculty_assignment import FacultyAssignment
from app.models.schedule import Schedule
from app.models.schedule_warning import ScheduleWarning as ScheduleWarningModel
from app.models.section import Section
from app.repositories import faculty as faculty_repo
from app.repositories import schedule_warning as warning_repo
from app.repositories import section as section_repo
from app.repositories import time_block as time_block_repo
from app.schemas.algorithm_input import AlgorithmInput
from app.schemas.algorithm_params import AlgorithmParameters
from app.schemas.course import CourseResponse
from app.services import course as course_service
from app.services import faculty as faculty_service
from app.services import semester as semester_service

logger = logging.getLogger(__name__)


# Time block validity


def _is_valid_for_assignment(tb) -> bool:
    """Return True only for time blocks that the auto-assignment algorithm should consider.

    Three categories of blocks are excluded:

    1. **3-hour blocks** — any block whose duration is 180 minutes or more.
       These are typically extended lab or exam slots and are not suitable
       for regular course auto-assignment.

    2. **Single-day blocks** — blocks that meet on only one weekday (e.g. "M", "F").
       Standard instructional blocks meet on at least two days per week.

    3. **Split blocks** — blocks that share a `block_group` letter with a sibling row.
       A split block is stored as two separate TimeBlock rows (e.g. "T 9:50–11:30"
       and "R 1:30–2:50") that together form one logical meeting pattern.  Each row
       has the same non-null `block_group` value to indicate the pairing.  Because
       the algorithm assigns one time block per section, split blocks cannot be
       represented correctly and must be excluded from automatic assignment.
    """
    start = tb.start_time
    end = tb.end_time

    # Duration check — reject blocks >= 3 hours
    duration_minutes = (end.hour * 60 + end.minute) - (start.hour * 60 + start.minute)
    if duration_minutes >= 180:
        return False

    # Single-day check — meeting_days is a string like "MWF" or "TR";
    # strip whitespace and count unique alphabetic characters
    unique_days = {c for c in tb.meeting_days.strip().upper() if c.isalpha()}
    if len(unique_days) == 1:
        return False

    # Split-block check — a non-null block_group means this row is one half of a
    # paired split block and should not be assigned independently by the algorithm
    if tb.block_group is not None:
        return False

    return True


# Status helpers


def _set_status(db, schedule_id: int, status: str, error_message: str | None = None):
    """Update schedule status and timestamps."""
    schedule = db.query(Schedule).filter(Schedule.schedule_id == schedule_id).first()
    if schedule:
        schedule.status = status
        if status == ScheduleStatus.RUNNING:
            schedule.started_at = datetime.now(UTC)
            schedule.completed_at = None
        elif status in (ScheduleStatus.GENERATED, ScheduleStatus.FAILED):
            schedule.completed_at = datetime.now(UTC)
        schedule.error_message = error_message
        db.commit()


# Warning persistence — respects dismissed warnings


def _persist_warnings(
    db,
    schedule_id,
    phase2_warnings,
    phase2_warning_section_ids,
    unmatched_assignments,
    algo_to_db_section_id,
):
    """Persist warnings, preserving dismissed ones and skipping duplicates.

    ``algo_to_db_section_id`` maps each algorithm-internal section id to the real DB
    section id that was just written, so row-level warnings land on the right row.
    """
    # Load all existing warnings (including dismissed)
    existing = warning_repo.get_by_schedule(db, schedule_id, include_dismissed=True)

    # Build set of dismissed warning keys so we don't re-create them.
    # section_id is part of the key so per-section dismissals survive across runs.
    dismissed_keys = {(w.type, w.section_id, w.course_id, w.faculty_nuid, w.time_block_id) for w in existing if w.dismissed}

    # Delete only non-dismissed warnings (dismissed ones survive re-runs)
    for w in existing:
        if not w.dismissed:
            db.delete(w)

    count = 0

    # Persist Phase 2 warnings (time block assignment issues)
    for w, algo_sid in zip(phase2_warnings, phase2_warning_section_ids, strict=True):
        real_sid = algo_to_db_section_id.get(algo_sid) if algo_sid is not None else None
        type_value = w.Type.value if w.Type else "unknown"
        key = (type_value, real_sid, w.CourseID, w.FacultyID, w.BlockID)
        if key in dismissed_keys:
            continue
        db.add(
            ScheduleWarningModel(
                schedule_id=schedule_id,
                section_id=real_sid,
                type=type_value,
                severity=w.SeverityRank.value,
                message=w.Message,
                faculty_nuid=w.FacultyID,
                course_id=w.CourseID,
                time_block_id=w.BlockID,
            )
        )
        count += 1

    # Persist unmatched section warnings
    for a in unmatched_assignments:
        real_sid = algo_to_db_section_id.get(a.section_id)
        key = (WarningType.INSUFFICIENT_FACULTY_SUPPLY.value, real_sid, a.course_id, None, None)
        if key in dismissed_keys:
            continue
        db.add(
            ScheduleWarningModel(
                schedule_id=schedule_id,
                section_id=real_sid,
                type=WarningType.INSUFFICIENT_FACULTY_SUPPLY.value,
                severity=str(WarningType.INSUFFICIENT_FACULTY_SUPPLY.severity.value),
                message=f"Section {a.section_id} unmatched: {a.unmatched_reason}",
                course_id=a.course_id,
            )
        )
        count += 1

    logger.info(f"Persisted {count} warnings ({len(dismissed_keys)} dismissed preserved)")


def _persist_per_section_warnings(db, schedule_id: int, section_ids: list[int]) -> int:
    """Run error_check on each section and stage ScheduleWarning rows (no commit)."""
    from app.services import section as section_service

    # Refresh schedule so its sections relationship reflects the just-written rows.
    schedule = db.query(Schedule).filter(Schedule.schedule_id == schedule_id).first()
    if schedule is not None:
        db.refresh(schedule)

    count = 0
    for sid in section_ids:
        section = section_repo.get_by_id(db, sid)
        if section is None:
            continue
        for wt in section_service.error_check(db, section):
            db.add(
                ScheduleWarningModel(
                    schedule_id=schedule_id,
                    section_id=sid,
                    type=wt.value,
                    severity=str(wt.severity.value),
                    message=wt.value,
                )
            )
            count += 1
    logger.info(f"Persisted {count} per-section warnings")
    return count


# Generate — full run from scratch


def run_algorithm_task(schedule_id: int, parameters: AlgorithmParameters):
    """Full scheduling pipeline — runs as a background task."""
    db = SessionLocal()
    try:
        _run_algorithm(db, schedule_id, parameters)
        _set_status(db, schedule_id, ScheduleStatus.GENERATED)
    except Exception as e:
        logger.error(f"Algorithm failed for schedule {schedule_id}: {e}")
        try:
            db.rollback()
            _set_status(db, schedule_id, ScheduleStatus.FAILED, str(e)[:500])
        except Exception:
            logger.error(f"Failed to update status for schedule {schedule_id}")
    finally:
        db.close()


def _run_algorithm(db, schedule_id: int, parameters: AlgorithmParameters):
    # Step 1: Load courses from prior same-season schedule
    schedule = db.query(Schedule).filter(Schedule.schedule_id == schedule_id).first()
    if not schedule:
        raise ValueError(f"Schedule {schedule_id} not found")
    prior_semester_id = semester_service.get_last_year(db, schedule.semester_id)
    if prior_semester_id is None:
        raise ValueError(f"No prior same-season semester found for schedule {schedule_id}")
    courses = course_service.generate_course_list(db, prior_semester_id, schedule.campus)
    if not courses:
        raise ValueError(f"No courses found for schedule {schedule_id}")
    logger.info(f"Loaded {len(courses)} courses for schedule {schedule_id}")

    # Step 2: Expand sections
    sections = _expand_sections(courses)
    logger.info(f"Expanded to {len(sections)} section candidates")

    # Step 3: Load faculty profiles
    all_faculty = faculty_repo.get_all(db, active_only=True)
    if not all_faculty:
        raise ValueError("No active faculty found")
    nuids = [f.nuid for f in all_faculty]
    profiles = faculty_service.build_all_profiles(db, nuids)
    logger.info(f"Built {len(profiles)} faculty profiles")

    # Step 4: Load time blocks — filter out blocks that are invalid for auto-assignment
    # (3-hour duration, single-day, or split blocks).  Invalid blocks remain in the DB
    # and can still be assigned manually; they are simply excluded from the algorithm.
    all_time_blocks = time_block_repo.get_all(db)
    time_blocks = [tb for tb in all_time_blocks if _is_valid_for_assignment(tb)]
    logger.info(f"Loaded {len(all_time_blocks)} time blocks, {len(time_blocks)} valid for auto-assignment")

    # Step 5: Phase 1 — faculty-to-course matching
    algorithm_input = AlgorithmInput(
        OfferedCourses=courses,
        AllFaculty=profiles,
        TimeBlocks=[tb.time_block_id for tb in time_blocks],
        Parameters=parameters,
    )
    phase1_results = match_courses_to_faculty(sections, algorithm_input)
    matched = [a for a in phase1_results if a.is_matched]
    unmatched = [a for a in phase1_results if not a.is_matched]

    for a in unmatched:
        logger.warning(f"Section {a.section_id} (course {a.course_id}) unmatched: {a.unmatched_reason}")
    logger.info(f"Phase 1 complete: {len(matched)} matched, {len(unmatched)} unmatched")

    # Step 6: Bridge — CourseAssignment → MatchedAssignment
    course_lookup = {c.course_id: c for c in courses}
    matched_for_phase2 = [
        MatchedAssignment(
            section_id=a.section_id,
            course_id=a.course_id,
            faculty_nuid=a.faculty_nuid,
            department_code=(course_lookup[a.course_id].subject if a.course_id in course_lookup and course_lookup[a.course_id].subject else ""),
        )
        for a in matched
    ]
    faculty_time_preferences = {p.nuid: p.meeting_preferences for p in profiles}

    # Step 7: Phase 2 — time block assignment
    phase2_result = assign_time_blocks(
        matched_for_phase2,
        time_blocks,
        faculty_time_preferences,
        parameters=parameters,
    )
    placed = [a for a in phase2_result.assignments if a.time_block_id is not None]
    unplaced = [a for a in phase2_result.assignments if a.time_block_id is None]

    for w in phase2_result.warnings:
        logger.warning(f"Phase 2 warning: {w.Message}")
    logger.info(f"Phase 2 complete: {len(placed)} placed, {len(unplaced)} unplaced")

    # Step 8: Write sections to DB — all sections are written regardless of assignment status
    matched_lookup = {a.section_id: a for a in matched}
    section_number_tracker: dict[int, int] = {}
    sections_written = 0
    algo_to_db_section_id: dict[int, int] = {}

    # Matched sections (placed or unplaced) — write with faculty, time block optional
    for sa in phase2_result.assignments:
        original = matched_lookup.get(sa.section_id)
        if original is None:
            continue

        section_number_tracker[original.course_id] = section_number_tracker.get(original.course_id, 0) + 1
        section_obj = Section(
            schedule_id=schedule_id,
            course_id=original.course_id,
            time_block_id=sa.time_block_id,
            section_number=section_number_tracker[original.course_id],
            capacity=30,
        )
        db.add(section_obj)
        db.flush()
        algo_to_db_section_id[sa.section_id] = section_obj.section_id
        fa = FacultyAssignment(
            faculty_nuid=original.faculty_nuid,
            section_id=section_obj.section_id,
        )
        db.add(fa)
        sections_written += 1

    # Unmatched sections — write with no faculty and no time block
    for a in unmatched:
        section_number_tracker[a.course_id] = section_number_tracker.get(a.course_id, 0) + 1
        section_obj = Section(
            schedule_id=schedule_id,
            course_id=a.course_id,
            time_block_id=None,
            section_number=section_number_tracker[a.course_id],
            capacity=30,
        )
        db.add(section_obj)
        db.flush()
        algo_to_db_section_id[a.section_id] = section_obj.section_id
        sections_written += 1

    # Step 9: Persist warnings (respects dismissed)
    _persist_warnings(
        db,
        schedule_id,
        phase2_result.warnings,
        phase2_result.warning_section_ids,
        unmatched,
        algo_to_db_section_id,
    )
    _persist_per_section_warnings(db, schedule_id, list(algo_to_db_section_id.values()))

    db.commit()
    logger.info(f"Algorithm completed for schedule {schedule_id}: {sections_written} sections written")


# Regenerate — re-run on unassigned sections, preserving existing
def run_regenerate_task(schedule_id: int, parameters: AlgorithmParameters):
    """Regenerate — re-run algorithm on unassigned sections only."""
    db = SessionLocal()
    try:
        _run_regenerate(db, schedule_id, parameters)
        _set_status(db, schedule_id, ScheduleStatus.GENERATED)
    except Exception as e:
        logger.error(f"Regenerate failed for schedule {schedule_id}: {e}")
        try:
            db.rollback()
            _set_status(db, schedule_id, ScheduleStatus.FAILED, str(e)[:500])
        except Exception:
            logger.error(f"Failed to update status for schedule {schedule_id}")
    finally:
        db.close()


def _run_regenerate(db, schedule_id: int, parameters: AlgorithmParameters):
    # Step 1: Load all courses for this schedule
    courses = course_service.get_courses(db, schedule_id)
    if not courses:
        raise ValueError(f"No courses found for schedule {schedule_id}")

    # Step 2: Load existing sections (already assigned from previous run)
    existing_sections = section_repo.get_by_schedule(db, schedule_id)

    # Build constraints from existing assignments
    existing_course_counts: dict[int, int] = defaultdict(int)
    existing_faculty_tbs: dict[int, set[int]] = defaultdict(set)
    existing_dept_tb_counts: dict[tuple[str, int], int] = defaultdict(int)
    dept_section_totals: dict[str, int] = defaultdict(int)

    for section in existing_sections:
        existing_course_counts[section.course_id] += 1
        if section.time_block_id and section.faculty_assignments:
            for fa in section.faculty_assignments:
                existing_faculty_tbs[fa.faculty_nuid].add(section.time_block_id)
            dept = section.course.subject if hasattr(section.course, "subject") else ""
            if dept and section.time_block_id:
                existing_dept_tb_counts[(dept, section.time_block_id)] += 1

    # Step 3: Figure out which courses still need sections
    courses_needing = []
    for c in courses:
        existing = existing_course_counts.get(c.course_id, 0)
        needed = (c.section_count or 0) - existing
        if needed > 0:
            courses_needing.append(
                CourseResponse(
                    course_id=c.course_id,
                    subject=c.subject,
                    code=c.code,
                    name=c.name,
                    description=c.description,
                    credits=c.credits,
                    section_count=needed,
                    priority=c.priority,
                    qualified_faculty=c.qualified_faculty,
                )
            )

    if not courses_needing:
        logger.info(f"All sections already assigned for schedule {schedule_id}")
        return

    total_needed = sum(c.section_count for c in courses_needing)
    logger.info(f"Regenerate: {len(courses_needing)} courses need {total_needed} more sections")

    # Step 4: Build department totals (full schedule)
    for c in courses:
        dept = c.subject or ""
        dept_section_totals[dept] += c.section_count or 0

    # Step 5: Expand only the remaining sections
    sections = _expand_sections(courses_needing)

    # Step 6: Load faculty and time blocks
    all_faculty = faculty_repo.get_all(db, active_only=True)
    if not all_faculty:
        raise ValueError("No active faculty found")
    nuids = [f.nuid for f in all_faculty]
    profiles = faculty_service.build_all_profiles(db, nuids)
    # Apply same validity filter as the full run — exclude 3-hour, single-day,
    # and split blocks so regenerated sections land on standard time slots only.
    all_time_blocks = time_block_repo.get_all(db)
    time_blocks = [tb for tb in all_time_blocks if _is_valid_for_assignment(tb)]
    logger.info(f"Regenerate: {len(all_time_blocks)} time blocks loaded, {len(time_blocks)} valid for auto-assignment")

    # Step 7: Phase 1 — match remaining sections
    algorithm_input = AlgorithmInput(
        OfferedCourses=courses_needing,
        AllFaculty=profiles,
        TimeBlocks=[tb.time_block_id for tb in time_blocks],
        Parameters=parameters,
    )
    phase1_results = match_courses_to_faculty(sections, algorithm_input)
    matched = [a for a in phase1_results if a.is_matched]
    unmatched = [a for a in phase1_results if not a.is_matched]
    logger.info(f"Regenerate Phase 1: {len(matched)} matched, {len(unmatched)} unmatched")

    # Step 8: Bridge
    course_lookup = {c.course_id: c for c in courses_needing}
    matched_for_phase2 = [
        MatchedAssignment(
            section_id=a.section_id,
            course_id=a.course_id,
            faculty_nuid=a.faculty_nuid,
            department_code=(course_lookup[a.course_id].subject if a.course_id in course_lookup and course_lookup[a.course_id].subject else ""),
        )
        for a in matched
    ]
    faculty_time_preferences = {p.nuid: p.meeting_preferences for p in profiles}

    # Step 9: Phase 2 with existing constraints
    phase2_result = assign_time_blocks(
        matched_for_phase2,
        time_blocks,
        faculty_time_preferences,
        parameters=parameters,
        existing_faculty_time_blocks=dict(existing_faculty_tbs),
        initial_department_time_block_counts=dict(existing_dept_tb_counts),
        department_section_totals=dict(dept_section_totals),
    )
    placed = [a for a in phase2_result.assignments if a.time_block_id is not None]
    logger.info(f"Regenerate Phase 2: {len(placed)} placed, {len(phase2_result.warnings)} warnings")

    # Step 10: Write new sections to DB
    matched_lookup = {a.section_id: a for a in matched}

    # Continue section numbering from existing max
    section_number_tracker: dict[int, int] = {}
    for s in existing_sections:
        current = section_number_tracker.get(s.course_id, 0)
        section_number_tracker[s.course_id] = max(current, s.section_number)

    sections_written = 0
    algo_to_db_section_id: dict[int, int] = {}

    # Matched sections (placed or unplaced) — write with faculty, time block optional
    for sa in phase2_result.assignments:
        original = matched_lookup.get(sa.section_id)
        if original is None:
            continue

        section_number_tracker[original.course_id] = section_number_tracker.get(original.course_id, 0) + 1
        section_obj = Section(
            schedule_id=schedule_id,
            course_id=original.course_id,
            time_block_id=sa.time_block_id,
            section_number=section_number_tracker[original.course_id],
            capacity=30,
        )
        db.add(section_obj)
        db.flush()
        algo_to_db_section_id[sa.section_id] = section_obj.section_id
        fa = FacultyAssignment(
            faculty_nuid=original.faculty_nuid,
            section_id=section_obj.section_id,
        )
        db.add(fa)
        sections_written += 1

    # Unmatched sections — write with no faculty and no time block
    for a in unmatched:
        section_number_tracker[a.course_id] = section_number_tracker.get(a.course_id, 0) + 1
        section_obj = Section(
            schedule_id=schedule_id,
            course_id=a.course_id,
            time_block_id=None,
            section_number=section_number_tracker[a.course_id],
            capacity=30,
        )
        db.add(section_obj)
        db.flush()
        algo_to_db_section_id[a.section_id] = section_obj.section_id
        sections_written += 1

    # Step 11: Persist warnings (append to existing, respect dismissed)
    _persist_warnings(
        db,
        schedule_id,
        phase2_result.warnings,
        phase2_result.warning_section_ids,
        unmatched,
        algo_to_db_section_id,
    )
    _persist_per_section_warnings(db, schedule_id, list(algo_to_db_section_id.values()))

    db.commit()
    logger.info(f"Regenerate completed for schedule {schedule_id}: {sections_written} new sections written")
