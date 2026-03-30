"""Campus router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.campus import CampusResponse
from app.services import campus as campus_service

router = APIRouter(prefix="/campuses", tags=["campuses"])


@router.get("", response_model=list[CampusResponse])
def get_campuses(
    db: Session = Depends(get_db),
    name: str | None = None,
):
    """Retrieve all campuses, optionally filtered by name."""
    return campus_service.get_all(db, name=name)


@router.get("/{campus_id}", response_model=CampusResponse)
def get_campus(campus_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific campus by ID."""
    return campus_service.get_by_id(db, campus_id)
