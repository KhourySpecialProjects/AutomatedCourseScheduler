from sqlalchemy.orm import Session

from app.models.course import Course
from app.repositories import course as course_repo
from app.repositories import schedule as schedule_repo
from app.schemas.course import CourseCreate, CourseResponse, CourseUpdate


def _course_to_response(course: Course, section_count: int) -> CourseResponse:
    return CourseResponse(
        CourseID=course.course_id,
        CourseName=course.name,
        CourseDescription=course.description,
        CourseNo=None,
        CourseSubject=None,
        SectionCount=section_count,
        Priority=course.priority,
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


def get_course(
    db: Session, course_id: int, schedule_id: int | None = None
) -> CourseResponse | None:
    if schedule_id is not None and not schedule_repo.schedule_exists(db, schedule_id):
        raise ValueError("ScheduleID is invalid")
    course = course_repo.get_by_id(db, course_id)
    if course is None:
        return None
    section_count = course_repo.get_section_count(db, course_id, schedule_id)
    return _course_to_response(course, section_count)


def create_course(db: Session, body: CourseCreate) -> CourseResponse:
    course = Course(
        name=body.name,
        description=body.description,
        credits=body.credits,
        priority=body.priority,
    )
    course_repo.create(db, course)
    return _course_to_response(course, 0)


def update_course(
    db: Session, course_id: int, body: CourseUpdate
) -> CourseResponse | None:
    course = course_repo.get_by_id(db, course_id)
    if course is None:
        return None
    fields = body.model_fields_set
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
