"""Tests for parse_file in upload router."""
import os
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.enums import PreferenceLevel
from app.main import app
from app.models.course import Course
from app.models.faculty import Faculty
from app.routers.upload import (
    COURSE_OFFERINGS,
    COURSE_PREFERENCES,
    parse_file,
)

COURSE_PREFERENCES_CSV = os.path.join(
    os.path.dirname(__file__), "course_preferences.csv")
COURSE_OFFERINGS_CSV = os.path.join(
    os.path.dirname(__file__), "course_offerings.csv")

mock_course = Course()
mock_course.course_id = 42

mock_faculty = Faculty()
mock_faculty.nuid = 1001


def query_side_effect(model):
    mock_query = MagicMock()
    if model == Course:
        mock_query.filter.return_value.first.return_value = mock_course
    elif model == Faculty:
        mock_query.filter.return_value.first.return_value = mock_faculty
    return mock_query


mock_db = MagicMock()
mock_db.query.side_effect = query_side_effect


def make_upload_file(content: str):
    """Helper to simulate an UploadFile with CSV content."""
    mock_file = MagicMock()
    mock_file.file.read.return_value = content.encode("utf-8")
    return mock_file


def make_upload_file_from_disk(path: str):
    """Helper to simulate an UploadFile using a real file on disk."""
    with open(path, "rb") as f:
        raw = f.read()
    mock_file = MagicMock()
    mock_file.file.read.return_value = raw
    return mock_file


"""Asserts parse_file correctly validates csv preference entries
against the schema and returns expected model format.
"""


def test_parse_file_preferences_valid():
    preferences_csv = (
        "Faculty Name,Faculty ID,Course,Semester,Preference\n"
        "John Smith,1001,CS 3200,Fall 2026,Eager to teach\n"
    )
    offerings_csv = (
        "Course,Credit Hours,Description\n"
        "CS 2500,4,This course provides an overview of CS 2500 concepts.\n"
    )

    preferences_result = parse_file(make_upload_file(preferences_csv),
                                    COURSE_PREFERENCES, mock_db)
    offerings_result = parse_file(make_upload_file(
        offerings_csv), COURSE_OFFERINGS, mock_db)

    assert len(preferences_result) == 1
    assert len(offerings_result) == 1
    assert preferences_result[0]["faculty_nuid"] == 1001
    assert preferences_result[0]["course_id"] == 42
    assert preferences_result[0]["preference"] == PreferenceLevel.FIRST
    assert offerings_result[0]["name"] == "CS 2500"
    assert offerings_result[0]["credits"] == 4
    assert offerings_result[0]["description"] == (
        "This course provides an overview of CS 2500 concepts."
    )


"""Asserts parse_file throws an error when an unknown course
has been found in the provided file.
"""


def test_parse_file_preferences_course_not_found():
    csv_content = (
        "Faculty Name,Faculty ID,Course,Semester,Preference\n"
        "John Smith,1001,CS 3200,Fall 2026,Eager to teach\n"
    )

    def query_null_course_side_effefct(model):
        mock_query = MagicMock()
        if model == Course:
            mock_query.filter.return_value.first.return_value = None
        elif model == Faculty:
            mock_query.filter.return_value.first.return_value = mock_faculty
        return mock_query

    mock_db_local = MagicMock()
    mock_db_local.query.side_effect = query_null_course_side_effefct

    with pytest.raises(HTTPException) as exc:
        parse_file(make_upload_file(csv_content),
                   COURSE_PREFERENCES, mock_db_local)

    assert exc.value.status_code == 422


"""Asserts parse_file throws an error when an unknown course
has been found in the provided file.
"""


def test_parse_file_preferences_faculty_not_found():
    csv_content = (
        "Faculty Name,Faculty ID,Course,Semester,Preference\n"
        "John Smith,1001,CS 3200,Fall 2026,Eager to teach\n"
    )

    def query_null_faculty_side_effect(model):
        mock_query = MagicMock()
        if model == Course:
            mock_query.filter.return_value.first.return_value = mock_course
        elif model == Faculty:
            mock_query.filter.return_value.first.return_value = None
        return mock_query

    mock_db_local = MagicMock()
    mock_db_local.query.side_effect = query_null_faculty_side_effect

    with pytest.raises(HTTPException) as exc:
        parse_file(make_upload_file(csv_content),
                   COURSE_PREFERENCES, mock_db_local)

    assert exc.value.status_code == 422


"""Asserts parse_file throws an error when an unknown preference rank
has been found in the provided file.
"""


def test_parse_file_preferences_invalid_enum():
    csv_content = (
        "Faculty Name,Faculty ID,Course,Semester,Preference\n"
        "John Smith,1001,CS 3200,Fall 2026,Invalid value\n"
    )

    mock_db = MagicMock()

    with pytest.raises(HTTPException) as exc:
        parse_file(make_upload_file(csv_content), COURSE_PREFERENCES, mock_db)

    assert exc.value.status_code == 422


"""Asserts parse_file correctly validates csv preference entries
against the schema and returns expected model format.
Checked against real file with multiple entries.
"""


def test_parse_file_from_real_csv():
    mock_course = Course()
    mock_course.CourseId = 99
    mock_faculty = Faculty()
    mock_faculty.nuid = 1001

    def query_side_effect(model):
        mock_query = MagicMock()
        if model == Course:
            mock_query.filter.return_value.first.return_value = mock_course
        elif model == Faculty:
            mock_query.filter.return_value.first.return_value = mock_faculty
        return mock_query

    mock_db = MagicMock()
    mock_db.query.side_effect = query_side_effect

    preferences_result = parse_file(make_upload_file_from_disk(
        COURSE_PREFERENCES_CSV), COURSE_PREFERENCES, mock_db)
    offerings_result = parse_file(make_upload_file_from_disk(
        COURSE_OFFERINGS_CSV), COURSE_OFFERINGS, mock_db)

    assert isinstance(preferences_result, list)
    assert len(preferences_result) > 0
    assert all(
        "faculty_nuid" in entry
        and "course_id" in entry
        and "preference" in entry
        for entry in preferences_result
    )
    assert all(
        "name" in entry
        and "credits" in entry
        and "description" in entry
        for entry in offerings_result
    )


"""Assert POST /upload/faculty-preferences parses the CSV
and inserts rows into the DB.
"""


def test_upload_faculty_preferences():
    mock_db.reset_mock()

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    csv_content = (
        "Faculty Name,Faculty ID,Course,Semester,Preference\n"
        "John Smith,1001,CS 3200,Fall 2026,Eager to teach\n"
    )

    with TestClient(app) as client:
        response = client.post(
            "/upload/faculty-preferences",
            files={"file": ("preferences.csv",
                            csv_content.encode("utf-8"), "text/csv")},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()

    # Verify the exact rows passed to db.execute match the CSV contents
    _, inserted_rows = mock_db.execute.call_args[0]
    assert len(inserted_rows) == 1
    assert inserted_rows[0]["faculty_nuid"] == 1001
    assert inserted_rows[0]["course_id"] == 42
    assert inserted_rows[0]["preference"] == PreferenceLevel.FIRST


"""Assert POST /upload/faculty-preferences parses the CSV
and inserts rows into the DB.
"""


def test_upload_course_offerings():
    mock_db.reset_mock()

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    csv_content = (
        "Course,Credit Hours,Description\n"
        "CS 2500,4,This course provides an overview of cs 2500 concepts.\n"
    )

    with TestClient(app) as client:
        response = client.post(
            "/upload/courses",
            files={"file": ("offerings.csv",
                            csv_content.encode("utf-8"), "text/csv")},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()

    # Verify the exact rows passed to db.execute match the CSV contents
    _, inserted_rows = mock_db.execute.call_args[0]
    assert len(inserted_rows) == 1
    assert inserted_rows[0]["name"] == "CS 2500"
    assert inserted_rows[0]["credits"] == 4
    assert inserted_rows[0]["description"] == (
        "This course provides an overview of cs 2500 concepts."
    )


"""Asserts parse_file accepts files with correct headers."""


def test_validate_headers_preferences_valid():
    csv_content = (
        "Faculty Name,Faculty ID,Course,Semester,Preference\n"
        "John Smith,1001,CS 3200,Fall 2026,Eager to teach\n"
    )
    result = parse_file(make_upload_file(csv_content),
                        COURSE_PREFERENCES, mock_db)
    assert isinstance(result, list)


def test_validate_headers_offerings_valid():
    csv_content = (
        "Course,Credit Hours,Description\n"
        "CS 2500,4,Intro to CS.\n"
    )
    result = parse_file(make_upload_file(csv_content),
                        COURSE_OFFERINGS, mock_db)
    assert isinstance(result, list)


"""Asserts parse_file raises HTTPException when headers are wrong."""


def test_validate_headers_preferences_invalid():
    csv_content = (
        "Wrong Name,Faculty ID,Course,Semester,Preference\n"
        "John Smith,1001,CS 3200,Fall 2026,Eager to teach\n"
    )
    with pytest.raises(HTTPException) as exc:
        parse_file(make_upload_file(csv_content), COURSE_PREFERENCES, mock_db)
    assert exc.value.status_code == 422


def test_validate_headers_offerings_invalid():
    csv_content = (
        "Course,Credits,Description\n"
        "CS 2500,4,Intro to CS.\n"
    )
    with pytest.raises(HTTPException) as exc:
        parse_file(make_upload_file(csv_content), COURSE_OFFERINGS, mock_db)
    assert exc.value.status_code == 422
