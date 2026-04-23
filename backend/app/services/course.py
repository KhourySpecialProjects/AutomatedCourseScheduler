from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.schedule import Schedule
from app.repositories import course as course_repo
from app.repositories import schedule as schedule_repo
from app.repositories import semester as semester_repo
from app.schemas.course import CourseCreate, CourseResponse, CourseUpdate

HIGH_PRIORITY_COURSES = [
    "CS 1800",
    "CS 2000",
    "CS 2100",
    "CS 2700",
    "CS 2800",
    "CS 3000",
    "CS 3100",
    "CS 3200",
    "CS 3650",
    "CS 3800",
    "CS 4530",
    "CS 5001",
    "CS 5002",
    "CS 5004",
    "CS 5010",
    "DS 3000",
    "DS 4400",
    "CY 2550",
]


def _course_to_response(course: Course, section_count: int) -> CourseResponse:
    qualified_faculty = sum(1 for p in course.course_preferences if p.preference.to_int() <= 3)
    return CourseResponse(
        course_id=course.course_id,
        subject=course.subject,
        code=course.code,
        name=course.name,
        description=course.description,
        credits=course.credits,
        priority=course.priority,
        section_count=section_count,
        qualified_faculty=qualified_faculty,
    )


def get_courses(db: Session, schedule_id: int | None = None) -> list[CourseResponse]:
    if schedule_id is not None and not schedule_repo.schedule_exists(db, schedule_id):
        raise ValueError("ScheduleID is invalid")
    if schedule_id is not None:
        courses = course_repo.get_by_schedule(db, schedule_id)
    else:
        courses = course_repo.get_all(db)

    return [
        _course_to_response(
            course,
            course_repo.get_section_count(db, course.course_id, schedule_id),
        )
        for course in courses
    ]


def get_course(db: Session, course_id: int, schedule_id: int | None = None) -> CourseResponse | None:
    if schedule_id is not None and not schedule_repo.schedule_exists(db, schedule_id):
        raise ValueError("ScheduleID is invalid")
    course = course_repo.get_by_id(db, course_id)
    if course is None:
        return None
    section_count = course_repo.get_section_count(db, course_id, schedule_id)
    return _course_to_response(course, section_count)


def get_section_count(schedule: Schedule, courses: list[Course], new_courses: list[Course]) -> list[CourseResponse]:
    course_responses = []
    errors = []

    for course in courses:
        section_count = schedule_repo.total_section_count(schedule, course.course_id)

        if section_count == 0:
            errors.append(f"Course {course.name} not found in schedule with id {schedule.schedule_id}")

        response = _course_to_response(course, section_count)
        course_responses.append(response)

    for course in new_courses:
        response = _course_to_response(course, 1)
        course_responses.append(response)

    if errors:
        raise ValueError(errors)

    return course_responses


def sort_course_list(course_list: list[CourseResponse]) -> list[CourseResponse]:
    return sorted(course_list, key=lambda c: (not c.priority, c.qualified_faculty, c.code or 0))


def generate_course_list(db: Session, semester_id: int, campus_id: int) -> list[CourseResponse]:
    """Build the course list for a new schedule draft.

    Courses and section counts are copied directly from the prior same-season
    schedule's sections.  Courses in the offerings catalog that were not offered
    last year are not auto-added — they can be added manually after creation.

    Raises ValueError if no prior same-season schedule exists or if it has no
    sections — a prior schedule with historical data is required to bootstrap
    a new draft.
    """
    semester = semester_repo.get_by_id(db, semester_id)
    if semester is None:
        raise ValueError(f"Semester {semester_id} not found")

    # Only consider active schedules.  
    schedules = semester_repo.get_schedules(db, semester, campus_id, active_only=True)
    if len(schedules) > 1:
        raise ValueError(f"Semester {semester_id} has multiple schedules for campus {campus_id}; expected 1")

    courses = schedule_repo.get_courses(schedules[0])
    if not courses:
        raise ValueError(f"Prior schedule (id={schedules[0].schedule_id}) has no sections to copy from")

    return sort_course_list(get_section_count(schedules[0], courses, []))


def create_course(db: Session, body: CourseCreate) -> CourseResponse:
    course = Course(
        subject=body.subject,
        code=body.code,
        name=body.name,
        description=body.description,
        credits=body.credits,
        priority=body.priority,
    )
    course_repo.create(db, course)
    return _course_to_response(course, 0)


def update_course(db: Session, course_id: int, body: CourseUpdate) -> CourseResponse | None:
    course = course_repo.get_by_id(db, course_id)
    if course is None:
        return None
    fields = body.model_fields_set
    if "subject" in fields:
        if not body.subject:
            raise ValueError("Subject is invalid")
        course.subject = body.subject
    if "code" in fields:
        if body.code is None or body.code <= 0:
            raise ValueError("Code is invalid")
        course.code = body.code
    if "name" in fields:
        if not body.name:
            raise ValueError("Name is invalid")
        course.name = body.name
    if "description" in fields:
        if not body.description:
            raise ValueError("Description is invalid")
        course.description = body.description
    if "credits" in fields:
        if body.credits is None or body.credits < 0:
            raise ValueError("Credits is invalid")
        course.credits = body.credits
    if "priority" in fields:
        if body.priority is None:
            raise ValueError("Priority is invalid")
        course.priority = body.priority
    course_repo.save(db, course)
    section_count = course_repo.get_section_count(db, course_id, None)
    return _course_to_response(course, section_count)


def delete_course(db: Session, course_id: int) -> bool:
    course = course_repo.get_by_id(db, course_id)
    if course is None:
        return False
    if course_repo.get_section_count(db, course_id, None) > 0:
        raise ValueError("Course has sections and cannot be deleted")
    course_repo.delete(db, course)
    return True


def get_course_capacity(db: Session, course_id: int) -> int:
    capacity = course_repo.get_course_capacity(db, course_id)
    return capacity
