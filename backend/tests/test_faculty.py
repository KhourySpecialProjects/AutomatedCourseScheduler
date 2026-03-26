"""Tests for faculty router: GET /faculty and GET /faculty/{id}."""

from datetime import time

from app.core.enums import Campus, PreferenceLevel
from app.models import (
    Course,
    CoursePreference,
    Faculty,
    MeetingPreference,
    TimeBlock,
)


def test_get_faculty_empty(client, db_session):
    response = client.get("/faculty")
    assert response.status_code == 200
    assert response.json() == []


def test_get_faculty_returns_all(client, db_session):
    db_session.add_all(
        [
            Faculty(
                nuid=1001,
                first_name="Jane",
                last_name="Doe",
                email="jane@example.com",
                campus="Boston",
            ),
            Faculty(
                nuid=1002,
                first_name="John",
                last_name="Smith",
                email="john@example.com",
                campus="Boston",
            ),
        ]
    )
    db_session.commit()

    response = client.get("/faculty")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_faculty_filter_by_campus(client, db_session):
    db_session.add_all(
        [
            Faculty(
                nuid=1001,
                first_name="A",
                last_name="X",
                email="a@x.com",
                campus="Boston",
            ),
            Faculty(
                nuid=1002,
                first_name="B",
                last_name="Y",
                email="b@y.com",
                campus="Oakland",
            ),
        ]
    )
    db_session.commit()

    response = client.get("/faculty?campus=Boston")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["FirstName"] == "A"


def test_get_faculty_filter_active_only(client, db_session):
    db_session.add_all(
        [
            Faculty(
                nuid=1001,
                first_name="A",
                last_name="X",
                email="a@x.com",
                campus="Boston",
                active=True,
            ),
            Faculty(
                nuid=1002,
                first_name="B",
                last_name="Y",
                email="b@y.com",
                campus="Boston",
                active=False,
            ),
        ]
    )
    db_session.commit()

    response = client.get("/faculty?active_only=true")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["NUID"] == 1001


def test_get_faculty_profile(client, db_session):
    faculty = Faculty(
        nuid=1001,
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        title="Professor",
        campus="Boston",
    )
    db_session.add(faculty)
    db_session.commit()

    response = client.get(f"/faculty/{faculty.nuid}")
    assert response.status_code == 200
    data = response.json()
    assert data["nuid"] == 1001
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Doe"
    assert data["email"] == "jane@example.com"
    assert data["title"] == "Professor"
    assert data["campus"] == "Boston"
    assert "course_preferences" in data
    assert "meeting_preferences" in data


def test_get_faculty_profile_with_preferences(client, db_session):
    course = Course(name="Algorithms", description="Algo", credits=4)
    db_session.add(course)
    db_session.flush()

    faculty = Faculty(
        nuid=2001,
        first_name="John",
        last_name="Smith",
        email="john@example.com",
        title="Associate Professor",
        campus="Boston",
    )
    db_session.add(faculty)
    db_session.flush()

    tb = TimeBlock(
        meeting_days="MW",
        start_time=time(10, 0),
        end_time=time(11, 0),
        campus=Campus.BOSTON,
    )
    db_session.add(tb)
    db_session.flush()

    db_session.add(
        CoursePreference(
            faculty_nuid=faculty.nuid,
            course_id=course.course_id,
            preference=PreferenceLevel.FIRST,
        )
    )
    db_session.add(
        MeetingPreference(
            faculty_nuid=faculty.nuid,
            meeting_time=tb.time_block_id,
            preference=PreferenceLevel.SECOND,
        )
    )
    db_session.commit()

    response = client.get(f"/faculty/{faculty.nuid}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["course_preferences"]) == 1
    assert data["course_preferences"][0]["course_name"] == "Algorithms"
    assert data["course_preferences"][0]["preference"] == "Eager to teach"
    assert len(data["meeting_preferences"]) == 1
    assert data["meeting_preferences"][0]["preference"] == "Ready to teach"


def test_get_faculty_not_found(client, db_session):
    response = client.get("/faculty/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Faculty not found"
