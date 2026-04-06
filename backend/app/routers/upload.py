"""Upload router."""

import csv
import logging
from datetime import time

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy import insert, update
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.enums import Campus
from app.models.course import Course
from app.models.course_preference import CoursePreference
from app.models.faculty import Faculty
from app.models.meeting_preference import MeetingPreference
from app.models.time_block import TimeBlock
from app.schemas.course_offerings import CourseOfferingsSchema
from app.schemas.course_preferences import CoursePreferencesSchema
from app.schemas.meeting_preferences import MeetingPreferencesSchema
from app.schemas.upload import UploadResponse

router = APIRouter(prefix="/upload", tags=["upload"])
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COURSE_OFFERINGS = "Course Offerings"
COURSE_PREFERENCES = "Course Preferences"
TIME_PREFERENCES = "Time Preferences"


@router.post("/courses", response_model=UploadResponse)
def upload_courses(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a CSV file containing course offering data."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    try:
        to_insert = parse_file(file, COURSE_OFFERINGS, db)
        if to_insert:
            db.execute(insert(Course), to_insert)
            db.commit()
        else:
            return UploadResponse(
                status="success",
                message=("File does not contain any non-existing courses. Nothing inserted."),
                records_processed=len(to_insert),
                records_successful=len(to_insert),
            )
    except HTTPException as e:
        logger.error(f"Database error in upload_courses: {str(e)}")
        raise

    return UploadResponse(
        status="success",
        message="Courses uploaded successfully",
        records_processed=len(to_insert),
        records_successful=len(to_insert),
    )


@router.post("/faculty-preferences", response_model=UploadResponse)
def upload_faculty_preferences(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a CSV file containing faculty preference data."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    to_insert = []
    to_update = []
    try:
        result = parse_file(file, COURSE_PREFERENCES, db)
        to_insert.extend(result.get("inserts"))
        to_update.extend(result.get("updates"))
        if to_insert:
            db.execute(insert(CoursePreference), to_insert)
        if to_update:
            db.execute(update(CoursePreference), to_update)
        db.commit()
    except HTTPException as e:
        logger.error(f"Upload error in upload_faculty_preferences: {str(e)}")
        raise

    return UploadResponse(
        status="success",
        message="Faculty preferences updated successfully",
        records_processed=len(to_insert) + len(to_update),
        records_successful=len(to_insert) + len(to_update),
    )


@router.post("/time-preferences", response_model=UploadResponse)
def upload_time_preferences(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a CSV file containing faculty time preference data."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    to_insert = []
    to_update = []
    try:
        result = parse_file(file, TIME_PREFERENCES, db)
        to_insert.extend(result.get("inserts"))
        to_update.extend(result.get("updates"))
        if to_insert:
            db.execute(insert(MeetingPreference), to_insert)
        if to_update:
            db.execute(update(MeetingPreference), to_update)
        db.commit()
    except HTTPException as e:
        logger.error(f"Upload error in upload_time_preferences: {str(e)}")
        raise

    return UploadResponse(
        status="success",
        message="Faculty meeting preferences updated successfully",
        records_processed=len(to_insert) + len(to_update),
        records_successful=len(to_insert) + len(to_update),
    )


def parse_file(file, schema, db):
    content = file.file.read().decode("utf-8").splitlines()
    dialect = csv.Sniffer().sniff(content[0]) if content else csv.excel
    reader = csv.DictReader(content, dialect=dialect)
    headers_ok = validate_headers(reader.fieldnames, schema)
    if not headers_ok.get("valid"):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid column names {reader.fieldnames}. Expected {headers_ok.get('expected')}"
            ),
        )

    if schema == COURSE_OFFERINGS:
        return parse_course_offerings(db, reader)
    elif schema == COURSE_PREFERENCES:
        return parse_course_preferences(db, reader)
    elif schema == TIME_PREFERENCES:
        return parse_time_preferences(db, reader)
    else:
        logger.error(
            f"Unknown file content type {schema}. Expected one of: "
            f"{[COURSE_OFFERINGS, COURSE_PREFERENCES, TIME_PREFERENCES]}"
        )
        return


def format_time_block(meeting_days, start_time, end_time):
    def fmt(t: time) -> str:
        period = "a" if t.hour < 12 else "p"
        hour = t.hour % 12 or 12
        return f"{hour}:{t.minute:02d}{period}"

    return f"{meeting_days} {fmt(start_time)}-{fmt(end_time)}"


def parse_time_preferences(db, reader):
    inserts = []
    updates = []
    errors = []
    for i, row in enumerate(reader):
        try:
            normalized = normalize_headers(row, TIME_PREFERENCES)
            validated = MeetingPreferencesSchema(**normalized)

            segments = validated.normalize_meeting_time()
            for days, start_time, end_time in segments:
                logger.info(
                    f"Row {i}: parsed segment — days={days}, start={start_time}, end={end_time}"
                )

                time_block = (
                    db.query(TimeBlock)
                    .filter(
                        TimeBlock.meeting_days == days,
                        TimeBlock.start_time == start_time,
                        TimeBlock.end_time == end_time,
                    )
                    .first()
                )

                faculty = db.query(Faculty).filter(Faculty.nuid == validated.facultyId).first()

                if not time_block:
                    time_block = TimeBlock(
                        meeting_days=days,
                        start_time=start_time,
                        end_time=end_time,
                        campus=Campus.BOSTON,
                    )
                    db.add(time_block)
                    db.flush()

                elif not faculty:
                    errors.append(
                        f"Row {i}: faculty '{validated.facultyName}' "
                        f"with id '{validated.facultyId}' not found"
                    )
                    continue

                existing_pref = (
                    db.query(MeetingPreference)
                    .filter(
                        MeetingPreference.faculty_nuid == validated.facultyId,
                        MeetingPreference.meeting_time == time_block.time_block_id,
                    )
                    .first()
                )
                if existing_pref:
                    if existing_pref.preference != validated.preference:
                        updates.append(
                            {
                                "preference_id": existing_pref.preference_id,
                                "preference": validated.preference,
                            }
                        )
                else:
                    db_entry = validated.translate(time_block.time_block_id)
                    inserts.append(db_entry)
        except ValidationError as e:
            errors.append(f"Row {i}: {e.errors()}")

    if errors:
        raise HTTPException(status_code=422, detail=errors)

    return {"inserts": inserts, "updates": updates}


def parse_course_offerings(db, reader):
    table_entries = []
    errors = []
    for i, row in enumerate(reader):
        try:
            normalized = normalize_headers(row, COURSE_OFFERINGS)
            validated = CourseOfferingsSchema(**normalized)
            existing = db.query(Course).filter(Course.name == validated.courseName).first()
            if existing:
                logger.info(f"Row {i}: course '{validated.courseName}' already exists, skipping")
                continue
            db_entry = validated.translate()
            table_entries.append(db_entry)
        except ValidationError as e:
            errors.append(f"Row {i}: {e.errors()}")

    if errors:
        raise HTTPException(status_code=422, detail=errors)

    return table_entries


def parse_course_preferences(db, reader):
    inserts = []
    updates = []
    errors = []
    for i, row in enumerate(reader):
        try:
            normalized = normalize_headers(row, COURSE_PREFERENCES)
            validated = CoursePreferencesSchema(**normalized)
            course = db.query(Course).filter(Course.name == validated.course).first()
            faculty = db.query(Faculty).filter(Faculty.nuid == validated.facultyId).first()
            if not course:
                errors.append(f"Row {i}: course '{validated.course}' not found")
            elif not faculty:
                errors.append(
                    f"Row {i}: faculty '{validated.facultyName}' "
                    f"with id '{validated.facultyId}' not found"
                )
            else:
                existing_pref = (
                    db.query(CoursePreference)
                    .filter(
                        CoursePreference.faculty_nuid == validated.facultyId,
                        CoursePreference.course_id == course.course_id,
                    )
                    .first()
                )
                if existing_pref:
                    if existing_pref.preference != validated.preference:
                        updates.append(
                            {
                                "preference_id": existing_pref.preference_id,
                                "preference": validated.preference,
                            }
                        )
                else:
                    db_entry = validated.translate(course.course_id)
                    inserts.append(db_entry)
        except ValidationError as e:
            errors.append(f"Row {i}: {e.errors()}")

    if errors:
        raise HTTPException(status_code=422, detail=errors)

    return {"inserts": inserts, "updates": updates}


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
    elif schema == TIME_PREFERENCES:
        expected_headers = [
            "Semester",
            "Faculty Name",
            "Faculty ID",
            "Meetingtime",
            "Preference",
        ]
    else:
        logger.error(
            f"Unknown schema {schema}. Expected one of: "
            f"{[COURSE_OFFERINGS, COURSE_PREFERENCES, TIME_PREFERENCES]}"
        )

    valid = set(expected_headers) == set(headers)

    return {"expected": expected_headers, "valid": valid}


def normalize_headers(row, schema):
    if schema == COURSE_OFFERINGS:
        normalized = {
            "courseName": row["Course"],
            "credits": row["Credit Hours"],
            "description": row["Description"],
        }
    elif schema == COURSE_PREFERENCES:
        normalized = {
            "facultyName": row["Faculty Name"].strip(),
            "facultyId": row["Faculty ID"].strip(),
            "course": row["Course"].strip(),
            "semester": row["Semester"].strip(),
            "preference": row["Preference"].strip(),
        }
    elif schema == TIME_PREFERENCES:
        normalized = {
            "facultyName": row["Faculty Name"].strip(),
            "facultyId": row["Faculty ID"].strip(),
            "meetingTime": row["Meetingtime"].strip(),
            "semester": row["Semester"].strip(),
            "preference": row["Preference"].strip(),
        }
    return normalized
