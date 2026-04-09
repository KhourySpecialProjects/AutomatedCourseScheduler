"""Algorithm service — real implementation."""

import logging

from sqlalchemy.orm import Session

from app.algorithms.matching import _expand_sections, match_courses_to_faculty
from app.models.faculty_assignment import FacultyAssignment
from app.models.section import Section
from app.repositories import faculty as faculty_repo
from app.repositories import time_block as time_block_repo
from app.schemas.algorithm_input import AlgorithmInput
from app.schemas.algorithm_params import AlgorithmParameters
from app.services import course as course_service
from app.services import faculty as faculty_service

logger = logging.getLogger(__name__)


def run_algorithm_task(db: Session, schedule_id: int, parameters: AlgorithmParameters):
    # Step 1 — Load courses for this schedule
    courses = course_service.get_courses(db, schedule_id)
    if not courses:
        logger.warning(f"No courses found for schedule {schedule_id}, aborting.")
        return

    # Step 2 — Build section candidates in memory (no DB writes yet)
    sections = _expand_sections(courses)
    section_lookup = {s.section_id: s for s in sections}

    # Step 3 — Load all active faculty and build profiles
    all_faculty = faculty_repo.get_all(db, active_only=True)
    if not all_faculty:
        logger.warning("No active faculty found, aborting.")
        return
    nuids = [f.nuid for f in all_faculty]
    try:
        profiles = faculty_service.build_all_profiles(db, nuids)
    except ValueError as e:
        logger.error(f"Failed to build faculty profiles: {e}")
        return

    # Step 4 — Load time blocks for Phase 2
    time_blocks = time_block_repo.get_all(db)

    # Step 5 — Build faculty time preference lookup for Phase 2
    faculty_time_preferences = {
        profile.nuid: profile.meeting_preferences for profile in profiles
    }

    # Step 6 — Build AlgorithmInput and run Phase 1 (faculty matching)
    algorithm_input = AlgorithmInput(
        OfferedCourses=courses,
        AllFaculty=profiles,
        TimeBlocks=[tb.time_block_id for tb in time_blocks],
        Parameters=parameters,
    )
    phase1_assignments = match_courses_to_faculty(sections, algorithm_input)

    # Filter to matched only for Phase 2
    matched_assignments = [a for a in phase1_assignments if a.is_matched]
    unmatched = [a for a in phase1_assignments if not a.is_matched]

    for a in unmatched:
        logger.warning(
            f"Section for course {a.course_id} unmatched: {a.unmatched_reason}"
        )

    # Step 7 — Run Phase 2 (time block assignment)
    # NOTE: Saisri's assign_time_blocks will be imported here once her PR merges.
    # For now, time_block_id comes from SectionCandidate (None until Phase 2 is wired).
    # TODO: replace this block with assign_time_blocks() call after merge.
    section_time_blocks: dict[int, int | None] = {
        a.section_id: section_lookup[a.section_id].time_block_id
        for a in matched_assignments
    }

    # Step 8 — Write results to DB
    section_number_tracker: dict[int, int] = {}  # course_id -> incrementing section number

    for assignment in matched_assignments:
        candidate = section_lookup[assignment.section_id]
        time_block_id = section_time_blocks[assignment.section_id]

        if time_block_id is None:
            logger.warning(
                f"No time block assigned for section {assignment.section_id} "
                f"(course {assignment.course_id}), skipping DB write."
            )
            continue

        # Increment section number per course
        section_number_tracker[assignment.course_id] = (
            section_number_tracker.get(assignment.course_id, 0) + 1
        )
        section_number = section_number_tracker[assignment.course_id]

        # Create Section row
        section_obj = Section(
            schedule_id=schedule_id,
            course_id=assignment.course_id,
            time_block_id=time_block_id,
            section_number=section_number,
            capacity=30,  # TODO: pull from course data once capacity field exists
        )
        db.add(section_obj)
        db.flush()  # get real section_id from Postgres before creating FacultyAssignment

        # Create FacultyAssignment row
        fa = FacultyAssignment(
            faculty_nuid=assignment.faculty_nuid,
            section_id=section_obj.section_id,
        )
        db.add(fa)

    db.commit()
    logger.info(f"Algorithm completed for schedule {schedule_id}.")


def run_regenerate_task(db: Session, schedule_id: int, parameters: AlgorithmParameters):
    # TODO: load only unassigned sections for this schedule, run algorithm on those only
    # preserving existing assignments
    pass