"""Tests for parse_file in upload router."""

import os
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.enums import PreferenceLevel
from app.main import app
from app.models.course import Course
from app.models.course_preference import CoursePreference
from app.models.faculty import Faculty
from app.models.meeting_preference import MeetingPreference
from app.models.time_block import TimeBlock
from app.routers.upload import (
    COURSE_OFFERINGS,
    COURSE_PREFERENCES,
    TIME_PREFERENCES,
    parse_file,
)

COURSE_PREFERENCES_CSV = os.path.join(os.path.dirname(__file__), "course_preferences.csv")
COURSE_OFFERINGS_CSV = os.path.join(os.path.dirname(__file__), "course_offerings.csv")

mock_course = Course()
mock_course.course_id = 42

mock_faculty = Faculty()
mock_faculty.nuid = 1001


def query_side_effect(model):
    mock_query = MagicMock()
    if model == Course:
        mock_query.filter.return_value.first.return_value = None
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


def test_parse_file_offerings_valid():
    offerings_csv = (
        "Course Code,Course Name,Credit Hours,Description\n"
        "CS 2500,Fundamentals of Computer Science 1,4,"
        "This course provides an overview of CS 2500 concepts.\n"
    )

    offerings_result = parse_file(make_upload_file(offerings_csv), COURSE_OFFERINGS, mock_db)

    assert len(offerings_result) == 1
    assert offerings_result[0]["name"] == "Fundamentals of Computer Science 1"
    assert offerings_result[0]["subject"] == "CS"
    assert offerings_result[0]["code"] == "2500"
    assert offerings_result[0]["credits"] == 4
    assert offerings_result[0]["description"] == (
        "This course provides an overview of CS 2500 concepts."
    )


def test_parse_file_preferences_valid():
    def query_side_effect(model):
        mock_query = MagicMock()
        if model == Course:
            mock_query.filter.return_value.first.return_value = mock_course
        elif model == Faculty:
            mock_query.filter.return_value.first.return_value = mock_faculty
        elif model == CoursePreference:
            mock_query.filter.return_value.first.return_value = None
        return mock_query

    mock_db_local = MagicMock()
    mock_db_local.query.side_effect = query_side_effect

    preferences_csv = (
        "Faculty Name,Faculty ID,Course,Semester,Preference\n"
        "John Smith,1001,CS 3200,Fall 2026,Eager to teach\n"
        "John Doe,1002,CS 3200,Fall 2026,Eager to teach\n"
    )

    preferences_result = parse_file(
        make_upload_file(preferences_csv), COURSE_PREFERENCES, mock_db_local
    )
    inserts = preferences_result.get("inserts")
    available_faculty = preferences_result.get("available_faculty")
    assert inserts[0]["faculty_nuid"] == 1001
    assert inserts[0]["course_id"] == 42
    assert inserts[0]["preference"] == PreferenceLevel.EAGER
    assert available_faculty[1] == 1002


def test_parse_file_preferences_dups_found():
    mock_preference = CoursePreference()
    mock_preference.preference_id = 10
    mock_preference.preference = PreferenceLevel.READY

    def query_side_effect(model):
        mock_query = MagicMock()
        if model == Course:
            mock_query.filter.return_value.first.return_value = mock_course
        elif model == Faculty:
            mock_query.filter.return_value.first.return_value = mock_faculty
        elif model == CoursePreference:
            mock_query.filter.return_value.first.return_value = mock_preference
        return mock_query

    mock_db_local = MagicMock()
    mock_db_local.query.side_effect = query_side_effect

    preferences_csv = (
        "Faculty Name,Faculty ID,Course,Semester,Preference\n"
        "John Smith,1001,CS 3200,Fall 2026,Eager to teach\n"
    )

    preferences_result = parse_file(
        make_upload_file(preferences_csv), COURSE_PREFERENCES, mock_db_local
    )
    updates = preferences_result.get("updates")
    assert updates[0]["preference_id"] == 10
    assert updates[0]["preference"] == PreferenceLevel.EAGER


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
        parse_file(make_upload_file(csv_content), COURSE_PREFERENCES, mock_db_local)

    assert exc.value.status_code == 422


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
        parse_file(make_upload_file(csv_content), COURSE_PREFERENCES, mock_db_local)

    assert exc.value.status_code == 422


def test_parse_file_preferences_invalid_enum():
    csv_content = (
        "Faculty Name,Faculty ID,Course,Semester,Preference\n"
        "John Smith,1001,CS 3200,Fall 2026,Invalid value\n"
    )

    mock_db = MagicMock()

    with pytest.raises(HTTPException) as exc:
        parse_file(make_upload_file(csv_content), COURSE_PREFERENCES, mock_db)

    assert exc.value.status_code == 422


def test_parse_file_from_real_csv_offerings():
    mock_course = Course()
    mock_course.CourseId = 99
    mock_faculty = Faculty()
    mock_faculty.nuid = 1001

    def query_side_effect(model):
        mock_query = MagicMock()
        if model == Course:
            mock_query.filter.return_value.first.return_value = None
        elif model == Faculty:
            mock_query.filter.return_value.first.return_value = mock_faculty
        elif model == CoursePreference:
            mock_query.filter.return_value.first.return_value = None
        return mock_query

    mock_db = MagicMock()
    mock_db.query.side_effect = query_side_effect

    offerings_result = parse_file(
        make_upload_file_from_disk(COURSE_OFFERINGS_CSV), COURSE_OFFERINGS, mock_db
    )

    assert all(
        "name" in entry and "credits" in entry and "description" in entry
        for entry in offerings_result
    )


def test_parse_file_from_real_csv_preferences():
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
        elif model == CoursePreference:
            mock_query.filter.return_value.first.return_value = None
        return mock_query

    mock_db = MagicMock()
    mock_db.query.side_effect = query_side_effect

    preferences_result = parse_file(
        make_upload_file_from_disk(COURSE_PREFERENCES_CSV), COURSE_PREFERENCES, mock_db
    )

    assert isinstance(preferences_result.get("inserts"), list)
    assert isinstance(preferences_result.get("updates"), list)
    assert len(preferences_result) > 0
    assert all(
        "faculty_nuid" in entry and "course_id" in entry and "preference" in entry
        for entry in preferences_result.get("inserts")
    )


def test_upload_faculty_preferences():
    mock_preference = CoursePreference()
    mock_preference.preference_id = 10
    mock_preference.preference = PreferenceLevel.READY

    def query_side_effect(model):
        mock_query = MagicMock()
        if model == Course:
            mock_query.filter.return_value.first.return_value = mock_course
        elif model == Faculty:
            mock_query.filter.return_value.first.return_value = mock_faculty
        elif model == CoursePreference:
            mock_query.filter.return_value.first.return_value = None
        return mock_query

    mock_db_local = MagicMock()
    mock_db_local.query.side_effect = query_side_effect

    def override_get_db():
        yield mock_db_local

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: {"sub": "test-user"}

    csv_content = (
        "Faculty Name,Faculty ID,Course,Semester,Preference\n"
        "John Smith,1001,CS 3200,Fall 2026,Eager to teach\n"
    )

    with TestClient(app) as client:
        response = client.post(
            "/upload/faculty-preferences",
            files={"file": ("preferences.csv", csv_content.encode("utf-8"), "text/csv")},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    mock_db_local.execute.assert_called_once()
    mock_db_local.commit.assert_called_once()

    _, inserted_rows = mock_db_local.execute.call_args[0]
    assert len(inserted_rows) == 1
    assert inserted_rows[0]["faculty_nuid"] == 1001
    assert inserted_rows[0]["course_id"] == 42
    assert inserted_rows[0]["preference"] == PreferenceLevel.EAGER


def test_upload_course_offerings():
    mock_db.reset_mock()

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: {"sub": "test-user"}

    csv_content = (
        "Course Code,Course Name,Credit Hours,Description\n"
        "CS 2500,Fundamentals of Computer Science 1,4,"
        "This course provides an overview of cs 2500 concepts.\n"
    )

    with TestClient(app) as client:
        response = client.post(
            "/upload/courses",
            files={"file": ("offerings.csv", csv_content.encode("utf-8"), "text/csv")},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()

    _, inserted_rows = mock_db.execute.call_args[0]
    assert len(inserted_rows) == 1
    assert inserted_rows[0]["name"] == "Fundamentals of Computer Science 1"
    assert inserted_rows[0]["subject"] == "CS"
    assert inserted_rows[0]["code"] == "2500"
    assert inserted_rows[0]["credits"] == 4
    assert inserted_rows[0]["description"] == (
        "This course provides an overview of cs 2500 concepts."
    )


def test_validate_headers_preferences_valid():
    def query_side_effect(model):
        mock_query = MagicMock()
        if model == Course:
            mock_query.filter.return_value.first.return_value = mock_course
        elif model == Faculty:
            mock_query.filter.return_value.first.return_value = mock_faculty
        return mock_query

    mock_db_local = MagicMock()
    mock_db_local.query.side_effect = query_side_effect

    csv_content = (
        "Faculty Name,Faculty ID,Course,Semester,Preference\n"
        "John Smith,1001,CS 3200,Fall 2026,Eager to teach\n"
    )
    result = parse_file(make_upload_file(csv_content), COURSE_PREFERENCES, mock_db_local)
    assert isinstance(result, dict)


def test_validate_headers_offerings_valid():
    csv_content = (
        "Course Code,Course Name,Credit Hours,Description\nCS 2500,Intro to CS,4,Intro to CS.\n"
    )
    result = parse_file(make_upload_file(csv_content), COURSE_OFFERINGS, mock_db)
    assert isinstance(result, list)


def test_validate_headers_preferences_invalid():
    def query_side_effect(model):
        mock_query = MagicMock()
        if model == Course:
            mock_query.filter.return_value.first.return_value = None
        elif model == Faculty:
            mock_query.filter.return_value.first.return_value = mock_faculty
        return mock_query

    mock_db_local = MagicMock()
    mock_db_local.query.side_effect = query_side_effect
    csv_content = (
        "Wrong Name,Faculty ID,Course,Semester,Preference\n"
        "John Smith,1001,CS 3200,Fall 2026,Eager to teach\n"
    )
    with pytest.raises(HTTPException) as exc:
        parse_file(make_upload_file(csv_content), COURSE_PREFERENCES, mock_db_local)
    assert exc.value.status_code == 422


def test_validate_headers_offerings_invalid():
    csv_content = "Course,Credits,Description\nCS 2500,4,Intro to CS.\n"
    with pytest.raises(HTTPException) as exc:
        parse_file(make_upload_file(csv_content), COURSE_OFFERINGS, mock_db)
    assert exc.value.status_code == 422


mock_time_block = TimeBlock()
mock_time_block.time_block_id = 7


def test_parse_time_preferences_valid():
    def query_side_effect(model):
        mock_query = MagicMock()
        if model == TimeBlock:
            mock_query.filter.return_value.first.return_value = mock_time_block
        elif model == MeetingPreference:
            mock_query.filter.return_value.first.return_value = None
        return mock_query

    mock_db_local = MagicMock()
    mock_db_local.query.side_effect = query_side_effect

    csv_content = (
        "Semester,Faculty Name,Faculty ID,Meetingtime,Preference\n"
        "Fall 2026,John Smith,1001,MWR 8:00a-9:05a,Eager to teach\n"
        "Fall 2026,Eric Gerber,1002,MWR 8:00a-9:05a,Eager to teach\n"
    )

    result = parse_file(make_upload_file(csv_content), TIME_PREFERENCES, mock_db_local)
    inserts = result.get("inserts")
    available_faculty = result.get("available_faculty")
    assert len(inserts) == 2
    assert inserts[0]["faculty_nuid"] == 1001
    assert inserts[0]["meeting_time"] == 7
    assert inserts[0]["preference"] == PreferenceLevel.EAGER
    assert available_faculty[1] == 1002


def test_parse_time_preferences_dup_found():
    mock_existing_pref = MeetingPreference()
    mock_existing_pref.preference_id = 5
    mock_existing_pref.preference = PreferenceLevel.READY

    def query_side_effect(model):
        mock_query = MagicMock()
        if model == TimeBlock:
            mock_query.filter.return_value.first.return_value = mock_time_block
        elif model == MeetingPreference:
            mock_query.filter.return_value.first.return_value = mock_existing_pref
        return mock_query

    mock_db_local = MagicMock()
    mock_db_local.query.side_effect = query_side_effect

    csv_content = (
        "Semester,Faculty Name,Faculty ID,Meetingtime,Preference\n"
        "Fall 2026,John Smith,1001,MWR 8:00a-9:05a,Eager to teach\n"
    )

    result = parse_file(make_upload_file(csv_content), TIME_PREFERENCES, mock_db_local)
    updates = result.get("updates")
    assert len(updates) == 1
    assert updates[0]["preference_id"] == 5
    assert updates[0]["preference"] == PreferenceLevel.EAGER


def test_parse_time_preferences_invalid_enum():
    csv_content = (
        "Semester,Faculty Name,Faculty ID,Meetingtime,Preference\n"
        "Fall 2026,John Smith,1001,MWR 8:00a-9:05a,Invalid value\n"
    )

    mock_db_local = MagicMock()

    with pytest.raises(HTTPException) as exc:
        parse_file(make_upload_file(csv_content), TIME_PREFERENCES, mock_db_local)

    assert exc.value.status_code == 422


def test_parse_time_preferences_invalid_headers():
    csv_content = (
        "Wrong,Faculty Name,Faculty ID,Meetingtime,Preference\n"
        "Fall 2026,John Smith,1001,MWR 8:00a-9:05a,Eager to teach\n"
    )

    mock_db_local = MagicMock()

    with pytest.raises(HTTPException) as exc:
        parse_file(make_upload_file(csv_content), TIME_PREFERENCES, mock_db_local)

    assert exc.value.status_code == 422


def test_upload_time_preferences():
    def query_side_effect(model):
        mock_query = MagicMock()
        if model == TimeBlock:
            mock_query.filter.return_value.first.return_value = mock_time_block
        elif model == MeetingPreference:
            mock_query.filter.return_value.first.return_value = None
        return mock_query

    mock_db_local = MagicMock()
    mock_db_local.query.side_effect = query_side_effect

    def override_get_db():
        yield mock_db_local

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: {"sub": "test-user"}

    csv_content = (
        "Semester,Faculty Name,Faculty ID,Meetingtime,Preference\n"
        "Fall 2026,John Smith,1001,MWR 8:00a-9:05a,Eager to teach\n"
    )

    with TestClient(app) as client:
        response = client.post(
            "/upload/time-preferences",
            files={"file": ("time_prefs.csv", csv_content.encode("utf-8"), "text/csv")},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    mock_db_local.execute.assert_called_once()
    mock_db_local.commit.assert_called_once()

    _, inserted_rows = mock_db_local.execute.call_args[0]
    assert len(inserted_rows) == 1
    assert inserted_rows[0]["faculty_nuid"] == 1001
    assert inserted_rows[0]["meeting_time"] == 7
    assert inserted_rows[0]["preference"] == PreferenceLevel.EAGER
