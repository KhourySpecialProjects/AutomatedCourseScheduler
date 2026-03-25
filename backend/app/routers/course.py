"""Course router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.course import CourseResponse
from app.services import course as course_service

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=list[CourseResponse])
def get_courses(
    schedule_id: int | None = Query(
        None, description="Filter to courses with sections in this schedule"
    ),
    db: Session = Depends(get_db),
):
    "Retrieve all courses, optionally filtered by schedule"
    try:
        return course_service.get_courses(db, schedule_id=schedule_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(
    course_id: int,
    schedule_id: int | None = Query(
        None, description="Section count for this schedule only"
    ),
    db: Session = Depends(get_db),
):
    "Retrieve a course by ID with section count."
    try:
        course = course_service.get_course(db, course_id, schedule_id=schedule_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course
