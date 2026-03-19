"""Upload router."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session, insert
from app.models.course_preference import CoursePreference

from app.core.database import get_db
from app.schemas.upload import UploadResponse
import csv

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/courses", response_model=UploadResponse)
def upload_courses(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a CSV file containing course offering data."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a .csv")
    
    elif file.content_type != "text/csv":
        raise HTTPException(status_code=400, detail="Invalid document type")

    # elif file.size > ??:  TODO will add later idk what the size limit should be
    #     raise HTTPException(status_code=400, detail="File exceeds ?? ?b size limit")

    else:
        to_insert = parse_file(file)
        db.execute(insert(CoursePreference), to_insert)
        db.commit()

    raise HTTPException(status_code=501, detail="Not implemented yet")


# TODO implement file parsing function
"""
    Parses the given csv file and validates each entry
    
    Args: 
        file (File): The file to be read; must be .csv 
        
    Returns: 
        List of database entries to be inserted into CourseOfferings table as JSON objects

"""
def parse_file(file):
    table_entries = []
    with open('data.csv', mode='r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            print(row['ColumnName'])  # Access by header name
    return table_entries


@router.post("/faculty-preferences", response_model=UploadResponse)
def upload_faculty_preferences(
    file: UploadFile = File(...), db: Session = Depends(get_db)
):
    """Upload a CSV file containing faculty preference data."""
    # TODO: Implement CSV parsing and faculty preference ingestion
    raise HTTPException(status_code=501, detail="Not implemented yet")
