"""Faculty router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.faculty import FacultyProfileResponse, FacultyResponse
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


@router.get("/{nuid}", response_model=FacultyProfileResponse)
def get_faculty_profile(nuid: int, db: Session = Depends(get_db)):
    "Retrieve faculty profile with course and time preferences."
    faculty = faculty_service.get_faculty_profile(db, nuid)
    if faculty is None:
        raise HTTPException(status_code=404, detail="Faculty not found")
    return faculty
