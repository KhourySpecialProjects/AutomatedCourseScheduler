"""Course router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.course import Course
from app.models.section import Section
from app.schemas.course import CourseResponse

router = APIRouter(prefix="/courses", tags=["courses"])


def _course_to_response(course: Course, section_count: int) -> CourseResponse:
    return CourseResponse(
        CourseID=course.course_id,
        CourseName=course.name,
        CourseDescription=course.description,
        CourseNo=None,
        CourseSubject=None,
        SectionCount=section_count,
    )


@router.get("", response_model=list[CourseResponse])
def get_courses(
    schedule_id: int | None = Query(
        None, description="Filter to courses with sections in this schedule"
    ),
    db: Session = Depends(get_db),
):
    "Retrieve all courses, optionally filtered by schedule"
    if schedule_id is not None:
        subq = (
            select(Section.course_id)
            .where(Section.schedule_id == schedule_id)
            .distinct()
        )
        courses = db.query(Course).filter(Course.course_id.in_(subq)).all()
    else:
        courses = db.query(Course).all()

    result = []
    for c in courses:
        q = db.query(func.count(Section.section_id)).filter(
            Section.course_id == c.course_id
        )
        if schedule_id is not None:
            q = q.filter(Section.schedule_id == schedule_id)
        cnt = q.scalar() or 0
        result.append(_course_to_response(c, cnt))
    return result


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(
    course_id: int,
    schedule_id: int | None = Query(
        None, description="Section count for this schedule only"
    ),
    db: Session = Depends(get_db),
):
    "Retrieve a course by ID with section count."
    course = db.query(Course).filter(Course.course_id == course_id).first()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    q = db.query(func.count(Section.section_id)).filter(Section.course_id == course_id)
    if schedule_id is not None:
        q = q.filter(Section.schedule_id == schedule_id)
    cnt = q.scalar() or 0
    return _course_to_response(course, cnt)
