"""Course service — business logic."""

from sqlalchemy.orm import Session

from app.models.course import Course
from app.repositories import course as course_repo
from app.schemas.course import CourseResponse


def _course_to_response(course: Course, section_count: int) -> CourseResponse:
    return CourseResponse(
        CourseID=course.course_id,
        CourseName=course.name,
        CourseDescription=course.description,
        CourseNo=None,
        CourseSubject=None,
        SectionCount=section_count,
    )


def get_courses(db: Session, schedule_id: int | None = None) -> list[CourseResponse]:
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
    course = course_repo.get_by_id(db, course_id)
    if course is None:
        return None
    section_count = course_repo.get_section_count(db, course_id, schedule_id)
    return _course_to_response(course, section_count)
