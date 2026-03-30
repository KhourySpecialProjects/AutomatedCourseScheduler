"""Campus router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.campus import CampusCreate, CampusResponse, CampusUpdate
from app.services import campus as campus_service

router = APIRouter(prefix="/campuses", tags=["campuses"])


@router.get("", response_model=list[CampusResponse])
def get_all_campuses(
    db: Session = Depends(get_db),
    name: str | None = None,
):
    """Retrieve all campuses, optionally filtered by name."""
    return campus_service.get_all(db, name=name)


@router.get("/{campus_id}", response_model=CampusResponse)
def get_campus(campus_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific campus by ID."""
    return campus_service.get_by_id(db, campus_id)


@router.post("", response_model=CampusResponse, status_code=201)
def create_campus(campus: CampusCreate, db: Session = Depends(get_db)):
    """Create a new campus."""
    return campus_service.create(db, campus)


@router.put("/{campus_id}", response_model=CampusResponse)
def update_campus(campus_id: int, campus: CampusUpdate, db: Session = Depends(get_db)):
    """Update campus metadata (name, etc.)."""
    return campus_service.update(db, campus_id, campus)


@router.delete("/{campus_id}", status_code=204)
def delete_campus(campus_id: int, db: Session = Depends(get_db)):
    """Delete a campus."""
    return campus_service.delete(db, campus_id)
