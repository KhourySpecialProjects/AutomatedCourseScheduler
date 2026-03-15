"""Upload router."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.upload import UploadResponse

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/courses", response_model=UploadResponse)
def upload_courses(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a CSV file containing course offering data."""
    # TODO: Implement CSV parsing and course data ingestion
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/faculty-preferences", response_model=UploadResponse)
def upload_faculty_preferences(
    file: UploadFile = File(...), db: Session = Depends(get_db)
):
    """Upload a CSV file containing faculty preference data."""
    # TODO: Implement CSV parsing and faculty preference ingestion
    raise HTTPException(status_code=501, detail="Not implemented yet")
