"""Course router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.course import CourseResponse

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=list[CourseResponse])
def get_courses(db: Session = Depends(get_db)):
    """Retrieve all courses."""
    # TODO: Implement course listing
    raise HTTPException(status_code=501, detail="Not implemented yet")
