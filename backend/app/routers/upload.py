"""Upload router."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import insert
from app.models.course_preference import CoursePreference
from app.models.course import Course
from app.schemas.course_preferences import CoursePreferencesSchema
from app.schemas.course_offerings import CourseOfferingsSchema

from app.core.database import get_db
from app.schemas.upload import UploadResponse
from pydantic import ValidationError
import csv
import logging

router = APIRouter(prefix="/upload", tags=["upload"])
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COURSE_OFFERINGS = "Course Offerings"
COURSE_PREFERENCES = "Course Preferences"


"""

"""


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
        try:
            to_insert = parse_file(file, COURSE_OFFERINGS)
            db.execute(insert(Course), to_insert)
            db.commit()
        except HTTPException as e:
            logger.error(f"Database error in upload_courses: {str(e)}")
    return


@router.post("/faculty-preferences", response_model=UploadResponse)
def upload_faculty_preferences(
    file: UploadFile = File(...), db: Session = Depends(get_db)
):
    """Upload a CSV file containing faculty preference data."""
    # TODO: Implement CSV parsing and faculty preference ingestion

    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    elif file.content_type != "text/csv":
        raise HTTPException(status_code=400, detail="Invalid document type")

    # elif file.size > ??:  TODO will add later idk what the size limit should be
    #     raise HTTPException(status_code=400, detail="File exceeds ?? ?b size limit")

    else:
        try:
            to_insert = parse_file(file, COURSE_PREFERENCES, db)
            db.execute(insert(CoursePreference), to_insert)
            db.commit()
        except HTTPException as e:
            logger.error(
                f"Database error in upload_faculty_preferences: {str(e)}")
    return


"""
    Parses the given csv file and validates each entry

    Args:
        file (File): The file to be read; must be .csv
        schema (String): Specifies the contents of the given csv. Must be either Course Offerings or Course Preferences"
        db (Session): The current database session

    Returns:
        List of course offerings validated against the corresponding schema and translated into expected db model format
        parsed from the given file

"""


def parse_file(file, schema, db):
    table_entries = []
    content = file.file.read().decode("utf-8").splitlines()
    reader = csv.DictReader(content)

    for i, row in enumerate(reader):
        try:
            if schema == COURSE_OFFERINGS:
                validated = CourseOfferingsSchema(**row)
            elif schema == COURSE_PREFERENCES:
                normalized = {
                    "facultyName": row["Faculty Name"],
                    "facultyId": row["Faculty ID"],
                    "course": row["Course"],
                    "semester": row["Semester"],
                    "preference": row["Preference"],
                }
                validated = CoursePreferencesSchema(**normalized)
                course = db.query(Course).filter(
                    Course.CourseName == validated.course).first()
                if not course:
                    raise HTTPException(
                        status_code=422, detail=f"Row {i}: course '{validated.course}' not found")
                else:
                    db_entry = validated.translate(course.CourseID)
                    table_entries.append(db_entry)
            else:
                logger.error(
                    f"Unknown file content type {schema}. Expected one of: {[COURSE_OFFERINGS, COURSE_PREFERENCES]}")
                return

        except ValidationError as e:
            print(e.errors())
            print(row)
            raise HTTPException(
                status_code=422, detail=f"row: {i}, error:{e.errors()}")

    return table_entries
