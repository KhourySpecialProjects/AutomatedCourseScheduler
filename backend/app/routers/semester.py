"""Semester router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.database import get_db
from app.schemas.semester import SemesterCreate, SemesterResponse, SemesterUpdate
from app.services import semester as semester_service

router = APIRouter(prefix="/semesters", tags=["semesters"])


@router.post("", response_model=SemesterCreate, status_code=201)
def create_semester(
    semester: SemesterCreate, db: Session = Depends(get_db), _=Depends(require_admin)
):
    """Create a new semester."""
    return semester_service.create(db, semester)


@router.get("", response_model=list[SemesterResponse])
def get_all_semesters(db: Session = Depends(get_db)):
    """Get all semesters, with optional filtering by campus, semester name, or year."""
    return semester_service.get_all(db)


@router.get("/{semester_id}", response_model=SemesterResponse)
def get_semester(semester_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific semester."""
    return semester_service.get_by_id(db, semester_id)


@router.put("/{semester_id}", response_model=SemesterResponse)
def update_semester(
    semester_id: int,
    semester: SemesterUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Update semester metadata (name, complete status, etc.)."""
    return semester_service.update(db, semester_id, semester)


@router.delete("/{semester_id}", status_code=204)
def delete_semester(semester_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Delete a semester and all its sections."""
    semester_service.delete(db, semester_id)
