"""Faculty router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.faculty import (
    FacultyCreate,
    FacultyProfileResponse,
    FacultyResponse,
    FacultyUpdate,
)
from app.services import faculty as faculty_service

router = APIRouter(prefix="/faculty", tags=["faculty"])


@router.get("", response_model=list[FacultyResponse])
def get_faculty(
    campus: str | None = Query(None, description="Filter by campus name"),
    active_only: bool = Query(False, description="Filter to only active faculty"),
    db: Session = Depends(get_db),
):
    """Retrieve all faculty members."""
    return faculty_service.get_faculty(db, campus=campus, active_only=active_only)


@router.post("", response_model=FacultyResponse, status_code=201)
def create_faculty(faculty: FacultyCreate, db: Session = Depends(get_db)):
    """Create a new faculty member."""
    try:
        return faculty_service.create_faculty(db, faculty)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{nuid}", response_model=FacultyProfileResponse)
def get_faculty_profile(nuid: int, db: Session = Depends(get_db)):
    "Retrieve faculty profile with course and time preferences."
    faculty = faculty_service.get_faculty_profile(db, nuid)
    if faculty is None:
        raise HTTPException(status_code=404, detail="Faculty not found")
    return faculty


@router.patch("/{nuid}", response_model=FacultyResponse)
def update_faculty(nuid: int, faculty: FacultyUpdate, db: Session = Depends(get_db)):
    """Partially update faculty demographics and status."""
    try:
        updated = faculty_service.update_faculty(db, nuid, faculty)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if updated is None:
        raise HTTPException(status_code=404, detail="Faculty not found")
    return updated


@router.delete("/{nuid}", status_code=204)
def delete_faculty(nuid: int, db: Session = Depends(get_db)):
    """Delete a faculty member and their preferences and assignments."""
    deleted = faculty_service.delete_faculty(db, nuid)
    if not deleted:
        raise HTTPException(status_code=404, detail="Faculty not found")
    return None
