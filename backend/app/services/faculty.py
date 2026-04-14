import logging
import math
from datetime import time

from sqlalchemy.orm import Session

from app.core.enums import PreferenceLevel
from app.models.faculty import Faculty
from app.models.faculty_assignment import FacultyAssignment
from app.repositories import course as course_repo
from app.repositories import faculty as faculty_repo
from app.repositories import schedule as schedule_repo
from app.repositories import section as section_repo
from app.repositories import time_block as time_block_repo
from app.schemas.faculty import (
    FacultyCreate,
    FacultyProfileResponse,
    FacultyResponse,
    FacultyUpdate,
)
from app.schemas.section import CoursePreferenceInfo, MeetingPreferenceInfo

logger = logging.getLogger(__name__)


def _faculty_to_response(faculty: Faculty) -> FacultyResponse:
    return FacultyResponse(
        nuid=faculty.nuid,
        first_name=faculty.first_name,
        last_name=faculty.last_name,
        email=faculty.email,
        campus=faculty.campus,
        active=faculty.active,
        maxLoad=faculty.max_load,
    )


def get_faculty(
    db: Session, campus: int | None = None, active_only: bool = False
) -> list[FacultyResponse]:
    faculty_list = faculty_repo.get_all(db, campus=campus, active_only=active_only)
    return [_faculty_to_response(f) for f in faculty_list]


def create_faculty(db: Session, body: FacultyCreate) -> FacultyResponse:
    if faculty_repo.get_by_nuid(db, body.nuid) is not None:
        raise ValueError("NUID already exists")
    if faculty_repo.email_in_use_by_other(db, body.email, None):
        raise ValueError("Email already exists")
    faculty = Faculty(
        nuid=body.nuid,
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        campus=body.campus,
        active=body.active,
        max_load=body.max_load,
    )
    faculty_repo.create(db, faculty)
    return _faculty_to_response(faculty)


def update_faculty(db: Session, nuid: int, body: FacultyUpdate) -> FacultyResponse | None:
    faculty = faculty_repo.get_by_nuid(db, nuid)
    if faculty is None:
        return None
    fields = body.model_fields_set
    logger.error(f"FIELDS: {fields}")
    if "first_name" in fields:
        if not body.first_name:
            raise ValueError("FirstName is invalid")
        faculty.first_name = body.first_name
    if "last_name" in fields:
        if not body.last_name:
            raise ValueError("LastName is invalid")
        faculty.last_name = body.last_name
    if "email" in fields:
        if not body.email:
            raise ValueError("Email is invalid")
        if faculty_repo.email_in_use_by_other(db, body.email, nuid):
            raise ValueError("Email already exists")
        faculty.email = body.email
    if "campus" in fields:
        if body.campus is None:
            raise ValueError("Campus is invalid")
        faculty.campus = body.campus
    if "active" in fields:
        if body.active is None:
            raise ValueError("Active is invalid")
        faculty.active = body.active
    if "max_load" in fields:
        faculty.max_load = body.max_load
    faculty_repo.save(db, faculty)
    return _faculty_to_response(faculty)


def delete_faculty(db: Session, nuid: int) -> bool:
    faculty = faculty_repo.get_by_nuid(db, nuid)
    if faculty is None:
        return False
    faculty_repo.delete_with_dependencies(db, faculty)
    return True


def get_faculty_profile(db: Session, nuid: int) -> FacultyProfileResponse | None:
    faculty = faculty_repo.get_by_nuid_with_preferences(db, nuid)
    if faculty is None:
        raise ValueError(f"Faculty with id {nuid} not found")

    return FacultyProfileResponse(
        nuid=faculty.nuid,
        first_name=faculty.first_name,
        last_name=faculty.last_name,
        email=faculty.email,
        campus=faculty.campus,
        active=faculty.active,
        maxLoad=faculty.max_load,
        course_preferences=[
            CoursePreferenceInfo(
                course_id=cp.course_id,
                course_name=cp.course.name,
                preference=cp.preference.value,
            )
            for cp in faculty.course_preferences
        ],
        meeting_preferences=[
            MeetingPreferenceInfo(
                time_block_id=mp.meeting_time,
                preference=mp.preference.value,
            )
            for mp in faculty.meeting_preferences
        ],
    )


def format_time_block(meeting_days, start_time, end_time):
    def fmt(t: time) -> str:
        period = "a" if t.hour < 12 else "p"
        hour = t.hour % 12 or 12
        return f"{hour}:{t.minute:02d}{period}"

    return f"{meeting_days} {fmt(start_time)}-{fmt(end_time)}"


def time_block_to_string(db: Session, time_block_id: int) -> str:
    time_block = time_block_repo.get_by_id(db, time_block_id)
    meeting_time = format_time_block(
        time_block.meeting_days, time_block.start_time, time_block.end_time
    )
    return meeting_time


def normalize_buckets(facultyProfile: FacultyProfileResponse) -> FacultyProfileResponse:
    course_buckets = {level: [] for level in PreferenceLevel}
    meeting_time_buckets = {level: [] for level in PreferenceLevel}
    for cp in facultyProfile.course_preferences:
        course_buckets[cp.preference].append(cp)
    for mp in facultyProfile.meeting_preferences:
        meeting_time_buckets[mp.preference].append(mp)

    course_tiers = [
        course_buckets[PreferenceLevel.EAGER],
        course_buckets[PreferenceLevel.READY],
        course_buckets[PreferenceLevel.WILLING],
    ]
    course_filled = [t for t in course_tiers if t]

    meeting_time_tiers = [
        meeting_time_buckets[PreferenceLevel.EAGER],
        meeting_time_buckets[PreferenceLevel.READY],
        meeting_time_buckets[PreferenceLevel.WILLING],
    ]
    meeting_time_filled = [t for t in meeting_time_tiers if t]

    course_eager = course_filled[0] if len(course_filled) > 0 else []
    course_ready = course_filled[1] if len(course_filled) > 1 else []

    meeting_eager = meeting_time_filled[0] if len(meeting_time_filled) > 0 else []
    meeting_ready = meeting_time_filled[1] if len(meeting_time_filled) > 1 else []

    for cp in course_eager:
        cp.preference = PreferenceLevel.EAGER
    for cp in course_ready:
        cp.preference = PreferenceLevel.READY

    for mp in meeting_eager:
        mp.preference = PreferenceLevel.EAGER
    for mp in meeting_ready:
        mp.preference = PreferenceLevel.READY

    # If all course preferences are NOT_INTERESTED, flag for manual review
    if not course_filled:
        facultyProfile.needsAdminReview = True

    return facultyProfile


def get_average_max_load(
    db: Session, previous_assignments: list[FacultyAssignment], nuid: int
) -> int:
    semester_counts = {}
    for assignment in previous_assignments:
        section = section_repo.get_by_id(db, assignment.section_id)
        schedule = schedule_repo.get_by_id(db, section.schedule_id)
        semester = schedule.semester_id
        if semester not in semester_counts.keys():
            semester_counts[semester] = 1
        else:
            semester_counts[semester] += 1
    total_sems = len(semester_counts)
    total_sections = 0
    for sem_count in semester_counts.values():
        total_sections += sem_count
    print(total_sections / total_sems)
    average_load = math.floor((total_sections / total_sems) + 0.5)
    update_faculty(db, nuid, FacultyUpdate(max_load=average_load))
    return math.floor((total_sections / total_sems) + 0.5)


def process_assignments(
    db: Session, previous_assignments: list[FacultyAssignment], faculty: Faculty
) -> FacultyProfileResponse:
    course_preferences = []
    meeting_preferences = []
    unique_courses = []
    unique_meeting_times = []
    for assignment in previous_assignments:
        section = section_repo.get_by_id(db, assignment.section_id)
        course = course_repo.get_by_id(db, section.course_id)
        if course not in unique_courses:
            unique_courses.append(course)
            course_preferences.append(
                CoursePreferenceInfo(
                    course_id=section.course_id,
                    course_name=course.name,
                    preference=PreferenceLevel.EAGER,
                )
            )
        meeting_time = time_block_to_string(db, section.time_block_id)
        if meeting_time not in unique_meeting_times:
            unique_meeting_times.append(meeting_time)
            meeting_preferences.append(
                MeetingPreferenceInfo(
                    time_block_id=section.time_block_id, preference=PreferenceLevel.EAGER
                )
            )
    return FacultyProfileResponse(
        nuid=faculty.nuid,
        first_name=faculty.first_name,
        last_name=faculty.last_name,
        email=faculty.email,
        campus=faculty.campus,
        active=faculty.active,
        maxLoad=get_average_max_load(db, previous_assignments, faculty.nuid),
        course_preferences=course_preferences,
        meeting_preferences=meeting_preferences,
    )


def build_profile(db: Session, nuid: int) -> FacultyProfileResponse | None:
    existing_profile = get_faculty_profile(db, nuid)
    if existing_profile and (
        existing_profile.course_preferences or existing_profile.meeting_preferences
    ):
        return normalize_buckets(existing_profile)
    else:
        faculty = faculty_repo.get_by_nuid(db, nuid)
        if not faculty:
            return None
        previous_assignments = section_repo.get_by_instructor(db, nuid)
        if previous_assignments:
            return process_assignments(db, previous_assignments, faculty)
        else:
            return FacultyProfileResponse(
                nuid=faculty.nuid,
                first_name=faculty.first_name,
                last_name=faculty.last_name,
                email=faculty.email,
                campus=faculty.campus,
                active=faculty.active,
                maxLoad=3,
                needsAdminReview=True,
                course_preferences=[],
                meeting_preferences=[],
            )  # TODO send some kind of broadcast explaining why faculty review is required


def build_all_profiles(db: Session, faculty_ids: list[int]) -> list[FacultyProfileResponse]:
    profiles = []
    errors = []
    for faculty in faculty_ids:
        profile = build_profile(db, faculty)
        if not profile:
            errors.append(f"Faculty with id {faculty} not found")
        profiles.append(profile)
    if errors:
        raise ValueError(errors)

    return profiles
