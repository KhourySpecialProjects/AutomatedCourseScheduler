"""Algorithm service — runs as background task with own DB session."""

import logging
from datetime import datetime, timezone

from app.algorithms.matching import _expand_sections, match_courses_to_faculty
from app.algorithms.models import MatchedAssignment
from app.algorithms.time_assignment import assign_time_blocks
from app.core.database import SessionLocal
from app.core.enums import ScheduleStatus
from app.models.faculty_assignment import FacultyAssignment
from app.models.schedule import Schedule
from app.models.section import Section
from app.repositories import faculty as faculty_repo
from app.repositories import time_block as time_block_repo
from app.schemas.algorithm_input import AlgorithmInput
from app.schemas.algorithm_params import AlgorithmParameters
from app.services import course as course_service
from app.services import faculty as faculty_service

logger = logging.getLogger(__name__)


def _set_status(db, schedule_id: int, status: str, error_message: str | None = None):
    """Update schedule status and timestamps."""
    schedule = db.query(Schedule).filter(
        Schedule.schedule_id == schedule_id
    ).first()
    if schedule:
        schedule.status = status
        if status == ScheduleStatus.RUNNING:
            schedule.started_at = datetime.now(timezone.utc)
            schedule.completed_at = None
        elif status in (ScheduleStatus.GENERATED, ScheduleStatus.FAILED):
            schedule.completed_at = datetime.now(timezone.utc)
        schedule.error_message = error_message
        db.commit()


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
    # Step 1: Load courses
    courses = course_service.get_courses(db, schedule_id)
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

    # Step 4: Load time blocks
    time_blocks = time_block_repo.get_all(db)
    logger.info(f"Loaded {len(time_blocks)} time blocks")

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
        logger.warning(
            f"Section {a.section_id} (course {a.course_id}) "
            f"unmatched: {a.unmatched_reason}"
        )
    logger.info(
        f"Phase 1 complete: {len(matched)} matched, {len(unmatched)} unmatched"
    )

    # Step 6: Bridge — CourseAssignment → MatchedAssignment
    course_name_lookup = {c.course_id: c for c in courses}

    matched_for_phase2 = [
        MatchedAssignment(
            section_id=a.section_id,
            course_id=a.course_id,
            faculty_nuid=a.faculty_nuid,
            department_code=(
                course_name_lookup[a.course_id].subject
                if a.course_id in course_name_lookup
                and course_name_lookup[a.course_id].subject
                else ""
            ),
        )
        for a in matched
    ]

    faculty_time_preferences = {
        profile.nuid: profile.meeting_preferences for profile in profiles
    }

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
    logger.info(
        f"Phase 2 complete: {len(placed)} placed, {len(unplaced)} unplaced"
    )

    # Step 8: Write results to DB
    matched_lookup = {a.section_id: a for a in matched}
    section_number_tracker: dict[int, int] = {}
    sections_written = 0

    for sa in phase2_result.assignments:
        if sa.time_block_id is None:
            logger.warning(
                f"No time block for section {sa.section_id}, skipping."
            )
            continue

        original = matched_lookup.get(sa.section_id)
        if original is None:
            continue

        section_number_tracker[original.course_id] = (
            section_number_tracker.get(original.course_id, 0) + 1
        )

        section_obj = Section(
            schedule_id=schedule_id,
            course_id=original.course_id,
            time_block_id=sa.time_block_id,
            section_number=section_number_tracker[original.course_id],
            capacity=30,
        )
        db.add(section_obj)
        db.flush()

        fa = FacultyAssignment(
            faculty_nuid=original.faculty_nuid,
            section_id=section_obj.section_id,
        )
        db.add(fa)
        sections_written += 1

    db.commit()
    logger.info(
        f"Algorithm completed for schedule {schedule_id}: "
        f"{sections_written} sections written"
    )


def run_regenerate_task(schedule_id: int, parameters: AlgorithmParameters):
    """Regenerate — re-run on unassigned sections only."""
    db = SessionLocal()
    try:
        logger.info(
            f"Regenerate not yet implemented for schedule {schedule_id}"
        )
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