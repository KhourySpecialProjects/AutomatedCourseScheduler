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
    campus_id: int | None = None,
    campus_name: str | None = None,
):
    """Retrieve all campuses, with optional filters."""
    return campus_service.get_all(db, campus_id=campus_id, campus_name=campus_name)
