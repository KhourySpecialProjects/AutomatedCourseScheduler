"""Upload router."""

import csv
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy import insert
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.course import Course
from app.models.course_preference import CoursePreference
from app.models.faculty import Faculty
from app.schemas.course_offerings import CourseOfferingsSchema
from app.schemas.course_preferences import CoursePreferencesSchema
from app.schemas.upload import UploadResponse

router = APIRouter(prefix="/upload", tags=["upload"])
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COURSE_OFFERINGS = "Course Offerings"
COURSE_PREFERENCES = "Course Preferences"


"""
    Upload a CSV file containing course offering data.

    Params: None
    Body:
        - expects one file in request body with key "file"
        - Each row should contain information for one course offering. Format must
          match expected schema.

    Result:
        - If valid, inserts all courses found in the file into DB Course table.

"""


@router.post("/courses", response_model=UploadResponse)
def upload_courses(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    elif file.content_type != "text/csv":
        raise HTTPException(status_code=400, detail="Invalid document type")

    else:
        try:
            to_insert = parse_file(file, COURSE_OFFERINGS, db)
            db.execute(insert(Course), to_insert)
            db.commit()
        except HTTPException as e:
            logger.error(f"Database error in upload_courses: {str(e)}")
            raise
        return UploadResponse(
            status="success",
            message="Courses uploaded successfully",
            records_processed=len(to_insert),
            records_successful=len(to_insert),
        )


"""
    Upload a CSV file containing faculty preference data.

    Params: None
    Body:
        - expects one file in request body with key "file"

"""


@router.post("/faculty-preferences", response_model=UploadResponse)
def upload_faculty_preferences(
    file: UploadFile = File(...), db: Session = Depends(get_db)
):
    """Upload a CSV file containing faculty preference data."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    elif file.content_type != "text/csv":
        raise HTTPException(status_code=400, detail="Invalid document type")

    else:
        try:
            to_insert = parse_file(file, COURSE_PREFERENCES, db)
            db.execute(insert(CoursePreference), to_insert)
            db.commit()
        except HTTPException as e:
            logger.error(
                f"Database error in upload_faculty_preferences: {str(e)}"
            )
            raise
        return UploadResponse(
            status="success",
            message="Faculty preferences uploaded successfully",
            records_processed=len(to_insert),
            records_successful=len(to_insert),
        )


"""
    Parses the given csv file and validates each entry

    Args:
        file (File): The file to be read; must be .csv
        schema (String): Specifies the contents of the given csv. Must be either
            Course Offerings or Course Preferences.
        db (Session): The current database session

    Returns:
        List of course offerings validated against the corresponding schema and
        translated into expected db model format parsed from the given file

"""


def parse_file(file, schema, db):
    table_entries = []
    content = file.file.read().decode("utf-8").splitlines()
    dialect = csv.Sniffer().sniff(content[0]) if content else csv.excel
    reader = csv.DictReader(content, dialect=dialect)
    headers_ok = validate_headers(reader.fieldnames, schema)
    if not headers_ok.get("valid"):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid column names {reader.fieldnames}. "
                f"Expected {headers_ok.get('expected')}"
            ),
        )

    for i, row in enumerate(reader):
        try:
            if schema == COURSE_OFFERINGS:
                normalized = {
                    "courseName": row["Course"],
                    "credits": row["Credit Hours"],
                    "description": row["Description"],
                }
                validated = CourseOfferingsSchema(**normalized)
                db_entry = validated.translate()
                table_entries.append(db_entry)
            elif schema == COURSE_PREFERENCES:
                normalized = {
                    "facultyName": row["Faculty Name"].strip(),
                    "facultyId": row["Faculty ID"].strip(),
                    "course": row["Course"].strip(),
                    "semester": row["Semester"].strip(),
                    "preference": row["Preference"].strip(),
                }
                validated = CoursePreferencesSchema(**normalized)
                course = db.query(Course).filter(
                    Course.name == validated.course
                ).first()
                faculty = db.query(Faculty).filter(
                    Faculty.nuid == validated.facultyId
                ).first()
                if not course:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Row {i}: course '{validated.course}' not found",
                    )
                elif not faculty:
                    raise HTTPException(
                        status_code=422,
                        detail=(
                            f"Row {i}: faculty '{validated.facultyName}' "
                            f"with id '{validated.facultyId}' not found"
                        ),
                    )
                else:
                    db_entry = validated.translate(course.course_id)
                    table_entries.append(db_entry)
            else:
                logger.error(
                    f"Unknown file content type {schema}. "
                    f"Expected one of: {[COURSE_OFFERINGS, COURSE_PREFERENCES]}"
                )
                return

        except ValidationError as e:
            print(e.errors())
            print(row)
            raise HTTPException(
                status_code=422, detail=f"row: {i}, error:{e.errors()}"
            ) from e

    return table_entries


"""
    Validates the given column headers against the expected schema

    Args:
        headers (List[String]): The column headers
        schema (String): Specifies the contents of the origin csv file. Must be
            either Course Offerings or Course Preferences.

    Returns:
        A dict with two keys:
            - expected (List[String]): The headers expected for the provided schema
            - valid (Boolean): True if headers match expected schema, False otherwise
"""


def validate_headers(headers, schema):
    if schema == COURSE_OFFERINGS:
        expected_headers = ["Course", "Credit Hours", "Description"]
    elif schema == COURSE_PREFERENCES:
        expected_headers = [
            "Faculty Name",
            "Faculty ID",
            "Course",
            "Semester",
            "Preference",
        ]
    else:
        logger.error(
            f"Unknown schema {schema}. "
            f"Expected one of: {[COURSE_OFFERINGS, COURSE_PREFERENCES]}"
        )

    valid = set(expected_headers) == set(headers)

    return {"expected": expected_headers, "valid": valid}
