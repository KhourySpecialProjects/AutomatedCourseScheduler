"""Faculty router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.faculty import FacultyResponse

router = APIRouter(prefix="/faculty", tags=["faculty"])


@router.get("", response_model=list[FacultyResponse])
def get_faculty(
    campus_id: int | None = Query(None, description="Filter by campus ID"),
    active_only: bool = Query(False, description="Filter to only active faculty"),
    db: Session = Depends(get_db),
):
    """Retrieve all faculty members."""
    # TODO: Implement faculty listing with filters
    raise HTTPException(status_code=501, detail="Not implemented yet")
