"""Campus router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.campus import CampusResponse

# from app.services import campus as campus_service

router = APIRouter(prefix="/campuses", tags=["campuses"])


@router.get("", response_model=list[CampusResponse])
def get_campuses(db: Session = Depends(get_db)):
    """Retrieve all campuses."""
    # return campus_service.get_all(db)
