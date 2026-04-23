"""Course router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.course import CourseCreate, CourseResponse, CourseUpdate
from app.services import course as course_service

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=list[CourseResponse])
def get_courses(
    schedule_id: int | None = Query(None, description="Filter to courses with sections in this schedule"),
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
    schedule_id: int | None = Query(None, description="Section count for this schedule only"),
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


@router.post("", response_model=CourseResponse, status_code=201)
def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    """Create a new course."""
    try:
        return course_service.create_course(db, course)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="A course with this subject and code already exists") from e


@router.patch("/{course_id}", response_model=CourseResponse)
def update_course(course_id: int, course: CourseUpdate, db: Session = Depends(get_db)):
    """Partially update a course."""
    try:
        updated = course_service.update_course(db, course_id, course)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if updated is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return updated


@router.delete("/{course_id}", status_code=204)
def delete_course(course_id: int, db: Session = Depends(get_db)):
    """Delete a course with no sections."""
    try:
        deleted = course_service.delete_course(db, course_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not deleted:
        raise HTTPException(status_code=404, detail="Course not found")
    return None
