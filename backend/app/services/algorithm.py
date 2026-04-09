"""Algorithm service — real implementation."""

import logging

from sqlalchemy.orm import Session

from app.algorithms.matching import _expand_sections, match_courses_to_faculty
from app.models.section import Section
from app.models.faculty_assignment import FacultyAssignment
from app.repositories import faculty as faculty_repo
from app.repositories import section as section_repo
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
        logger.warning(f"No active faculty found, aborting.")
        return
    nuids = [f.nuid for f in all_faculty]
    try:
        profiles = faculty_service.build_all_profiles(db, nuids)
    except ValueError as e:
        logger.error(f"Failed to build faculty profiles: {e}")
        return

    # Step 4 — Build AlgorithmInput and run matching
    algorithm_input = AlgorithmInput(
        OfferedCourses=courses,
        AllFaculty=profiles,
        TimeBlocks=[],
        Parameters=parameters,
    )
    assignments = match_courses_to_faculty(sections, algorithm_input)

    # Step 5 — Write results to DB
    section_number_tracker: dict[int, int] = {}  # course_id -> section number counter

    for assignment in assignments:
        if not assignment.is_matched:
            logger.warning(
                f"Section for course {assignment.course_id} unmatched: "
                f"{assignment.unmatched_reason}"
            )
            continue

        candidate = section_lookup[assignment.section_id]

        # Track section numbers per course
        section_number_tracker[assignment.course_id] = (
            section_number_tracker.get(assignment.course_id, 0) + 1
        )
        section_number = section_number_tracker[assignment.course_id]

        # Create Section row
        section_obj = Section(
            schedule_id=schedule_id,
            course_id=assignment.course_id,
            time_block_id=candidate.time_block_id,
            section_number=section_number,
            capacity=30,  # TODO: pull from course data once capacity field exists
        )
        db.add(section_obj)
        db.flush()  # get section_obj.section_id from Postgres before creating assignment

        # Create FacultyAssignment row
        fa = FacultyAssignment(
            faculty_nuid=assignment.faculty_nuid,
            section_id=section_obj.section_id,
        )
        db.add(fa)

    db.commit()
    logger.info(f"Algorithm completed for schedule {schedule_id}.")