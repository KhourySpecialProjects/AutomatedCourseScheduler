"""Algorithm service"""

import logging

from app.algorithms.matching import _expand_sections, match_courses_to_faculty
from app.algorithms.models import MatchedAssignment
from app.algorithms.time_assignment import assign_time_blocks
from app.core.database import SessionLocal
from app.models.faculty_assignment import FacultyAssignment
from app.models.section import Section
from app.repositories import faculty as faculty_repo
from app.repositories import time_block as time_block_repo
from app.schemas.algorithm_input import AlgorithmInput
from app.schemas.algorithm_params import AlgorithmParameters
from app.services import course as course_service
from app.services import faculty as faculty_service

logger = logging.getLogger(__name__)


def run_algorithm_task(schedule_id: int, parameters: AlgorithmParameters):
    """
    Full scheduling pipeline — runs as a background task.

    Phase 1: Faculty-to-course stable matching with displacement
    Phase 2: Time block assignment with 15% department cap
    Phase 3: Write results to DB as Section + FacultyAssignment rows
    """
    db = SessionLocal()
    try:
        _run_algorithm(db, schedule_id, parameters)
    except Exception as e:
        logger.error(f"Algorithm failed for schedule {schedule_id}: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def _run_algorithm(db, schedule_id: int, parameters: AlgorithmParameters):
    # =========================================================================
    # Step 1: Load courses for this schedule
    # =========================================================================
    # course_service.get_courses queries Course table filtered by schedule,
    # returns list[CourseResponse] with CourseID, SectionCount, Priority, etc.
    courses = course_service.get_courses(db, schedule_id)
    if not courses:
        logger.warning(f"No courses found for schedule {schedule_id}, aborting.")
        return

    logger.info(f"Loaded {len(courses)} courses for schedule {schedule_id}")

    # =========================================================================
    # Step 2: Expand courses into section candidates
    # =========================================================================
    # _expand_sections: list[CourseResponse] → list[SectionCandidate]
    # Each course with SectionCount=N produces N SectionCandidate objects.
    # Sections don't exist in DB yet — the algorithm creates them in Step 8.
    sections = _expand_sections(courses)
    logger.info(f"Expanded to {len(sections)} section candidates")

    # =========================================================================
    # Step 3: Load faculty and build profiles
    # =========================================================================
    # faculty_repo.get_all returns Faculty ORM objects.
    # build_all_profiles calls build_profile for each → FacultyProfileResponse
    # with course_preferences, meeting_preferences, computed maxLoad.
    # normalize_buckets is applied inside build_profile (Lainie problem fix).
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

    logger.info(f"Built {len(profiles)} faculty profiles")

    # =========================================================================
    # Step 4: Load time blocks
    # =========================================================================
    # TimeBlock model has: time_block_id, meeting_days, start_time, end_time
    time_blocks = time_block_repo.get_all(db)
    logger.info(f"Loaded {len(time_blocks)} time blocks")

    # =========================================================================
    # Step 5: Build AlgorithmInput and run Phase 1
    # =========================================================================
    # AlgorithmInput bundles everything the algorithm needs.
    # match_courses_to_faculty runs the priority queue with displacement:
    #   - Priority sections first, most constrained first
    #   - Cross-tier displacement (priority takes from non-priority)
    #   - Within-tier displacement (strict preference improvement only)
    #   - Must-have protection (priority sections can't be displaced)
    #   - Termination: max 2 × |sections| iterations
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
            f"Section {a.section_id} (course {a.course_id}) unmatched: {a.unmatched_reason}"
        )

    logger.info(f"Phase 1 complete: {len(matched)} matched, {len(unmatched)} unmatched")

    # =========================================================================
    # Step 6: Bridge — CourseAssignment → MatchedAssignment
    # =========================================================================
    # Phase 2 expects MatchedAssignment (frozen dataclass with department_code).
    # Only matched sections go to Phase 2 — unmatched don't get time blocks.
    course_name_lookup = {c.CourseID: c.CourseName or "" for c in courses}

    matched_for_phase2 = [
        MatchedAssignment(
            section_id=a.section_id,
            course_id=a.course_id,
            faculty_nuid=a.faculty_nuid,
            department_code=(
                course_name_lookup.get(a.course_id, "").split()[0].upper()
                if course_name_lookup.get(a.course_id)
                else ""
            ),
        )
        for a in matched
    ]

    # Build faculty time preference map for Phase 2
    faculty_time_preferences = {profile.nuid: profile.meeting_preferences for profile in profiles}

    # =========================================================================
    # Step 7: Run Phase 2 — Time Block Assignment
    # =========================================================================
    # assign_time_blocks: greedy assignment
    #   - Most constrained faculty first (fewest rated time prefs)
    #   - 15% department cap per time block
    #   - Day clustering to minimize faculty campus days
    #   - Returns TimeBlockAssignmentResult with .assignments and .warnings
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

    # =========================================================================
    # Step 8: Write results to DB
    # =========================================================================
    # For each placed section: create a Section row + FacultyAssignment row.
    # Unplaced sections (time_block_id=None) are skipped — Section.time_block_id
    # is NOT NULL in the DB, so we can't write them.
    # These will appear as missing sections for the scheduler to fill manually.

    # Lookup: section_id → original CourseAssignment (for course_id, faculty_nuid)
    matched_lookup = {a.section_id: a for a in matched}

    # Track section numbers per course (Section 1, 2, 3... of CS 3500)
    section_number_tracker: dict[int, int] = {}
    sections_written = 0

    for sa in phase2_result.assignments:
        # Skip unplaced — can't write to DB without time_block_id
        if sa.time_block_id is None:
            logger.warning(f"No time block for section {sa.section_id}, skipping DB write.")
            continue

        # Get the original Phase 1 assignment for this section
        original = matched_lookup.get(sa.section_id)
        if original is None:
            continue

        # Increment section number per course
        section_number_tracker[original.course_id] = (
            section_number_tracker.get(original.course_id, 0) + 1
        )
        section_number = section_number_tracker[original.course_id]

        # Create Section row
        section_obj = Section(
            schedule_id=schedule_id,
            course_id=original.course_id,
            time_block_id=sa.time_block_id,
            section_number=section_number,
            capacity=course_service.get_course_capacity(db, original.course_id),
        )
        db.add(section_obj)
        db.flush()  # get real section_id from Postgres

        # Create FacultyAssignment row
        fa = FacultyAssignment(
            faculty_nuid=original.faculty_nuid,
            section_id=section_obj.section_id,
        )
        db.add(fa)
        sections_written += 1

    db.commit()
    logger.info(
        f"Algorithm completed for schedule {schedule_id}: {sections_written} sections written to DB"
    )


def run_regenerate_task(schedule_id: int, parameters: AlgorithmParameters):
    """
    Regenerate — re-run algorithm on unassigned sections only,
    preserving existing manual assignments.
    """
    db = SessionLocal()
    try:
        # TODO: implement
        # 1. Load existing sections for schedule (already assigned)
        # 2. Load unassigned courses (no section row yet)
        # 3. Run algorithm on unassigned only, passing existing assignments
        #    as constraints (existing_faculty_time_blocks, initial_department_time_block_counts)
        # 4. Write new sections to DB
        logger.info(f"Regenerate not yet implemented for schedule {schedule_id}")
    except Exception as e:
        logger.error(f"Regenerate failed for schedule {schedule_id}: {e}")
        db.rollback()
        raise
    finally:
        db.close()
