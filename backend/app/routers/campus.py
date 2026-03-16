"""Campus router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.campus import CampusResponse

router = APIRouter(prefix="/campuses", tags=["campuses"])


@router.get("", response_model=list[CampusResponse])
def get_campuses(db: Session = Depends(get_db)):
    """Retrieve all campuses."""
    # TODO: Implement campus listing
    raise HTTPException(status_code=501, detail="Not implemented yet")
