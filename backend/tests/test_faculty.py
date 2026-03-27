"""Tests for faculty router: GET /faculty and GET /faculty/{id}."""

from datetime import time

from app.core.enums import Campus, PreferenceLevel, Semester
from app.models import (
    Course,
    CoursePreference,
    Faculty,
    FacultyAssignment,
    MeetingPreference,
    Schedule,
    Section,
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


def test_create_faculty_success(client, db_session):
    response = client.post(
        "/faculty",
        json={
            "nuid": 5001,
            "first_name": "Pat",
            "last_name": "Kim",
            "email": "pat.kim@example.edu",
            "campus": "Boston",
            "title": "Lecturer",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["NUID"] == 5001
    assert data["FirstName"] == "Pat"
    assert data["Email"] == "pat.kim@example.edu"
    assert data["Active"] is True


def test_create_faculty_duplicate_nuid_returns_400(client, db_session):
    db_session.add(
        Faculty(
            nuid=6001,
            first_name="A",
            last_name="B",
            email="a@b.edu",
            campus="Boston",
        )
    )
    db_session.commit()

    response = client.post(
        "/faculty",
        json={
            "nuid": 6001,
            "first_name": "C",
            "last_name": "D",
            "email": "other@b.edu",
            "campus": "Boston",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "NUID already exists"


def test_create_faculty_duplicate_email_returns_400(client, db_session):
    db_session.add(
        Faculty(
            nuid=6002,
            first_name="A",
            last_name="B",
            email="shared@b.edu",
            campus="Boston",
        )
    )
    db_session.commit()

    response = client.post(
        "/faculty",
        json={
            "nuid": 6003,
            "first_name": "C",
            "last_name": "D",
            "email": "shared@b.edu",
            "campus": "Boston",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already exists"


def test_patch_faculty_success(client, db_session):
    db_session.add(
        Faculty(
            nuid=7001,
            first_name="Old",
            last_name="Name",
            email="old@example.edu",
            campus="Boston",
            active=True,
        )
    )
    db_session.commit()

    response = client.patch(
        "/faculty/7001",
        json={
            "first_name": "New",
            "active": False,
            "title": "Professor",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["FirstName"] == "New"
    assert data["Active"] is False
    assert data["Title"] == "Professor"


def test_patch_faculty_not_found_returns_404(client, db_session):
    response = client.patch("/faculty/99999", json={"first_name": "X"})
    assert response.status_code == 404


def test_patch_faculty_duplicate_email_returns_400(client, db_session):
    db_session.add_all(
        [
            Faculty(
                nuid=8001,
                first_name="A",
                last_name="One",
                email="a1@example.edu",
                campus="Boston",
            ),
            Faculty(
                nuid=8002,
                first_name="B",
                last_name="Two",
                email="b2@example.edu",
                campus="Boston",
            ),
        ]
    )
    db_session.commit()

    response = client.patch(
        "/faculty/8002",
        json={"email": "a1@example.edu"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already exists"


def test_delete_faculty_success(client, db_session):
    db_session.add(
        Faculty(
            nuid=9001,
            first_name="Gone",
            last_name="Soon",
            email="gone@example.edu",
            campus="Boston",
        )
    )
    db_session.commit()

    response = client.delete("/faculty/9001")
    assert response.status_code == 204
    assert db_session.get(Faculty, 9001) is None


def test_delete_faculty_removes_preferences_and_assignments(client, db_session):
    course = Course(name="PL", description="PL", credits=4)
    tb = TimeBlock(
        meeting_days="MW",
        start_time=time(10, 0),
        end_time=time(11, 0),
        timezone="EST",
        campus=Campus.BOSTON,
    )
    faculty = Faculty(
        nuid=9002,
        first_name="Rich",
        last_name="Prefs",
        email="prefs@example.edu",
        campus="Boston",
    )
    db_session.add_all([course, tb, faculty])
    db_session.flush()
    schedule = Schedule(name="F24", semester=Semester.FALL, year=2024)
    db_session.add(schedule)
    db_session.flush()
    section = Section(
        schedule_id=schedule.schedule_id,
        time_block_id=tb.time_block_id,
        course_id=course.course_id,
        section_number=1,
        capacity=20,
    )
    db_session.add(section)
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
    db_session.add(
        FacultyAssignment(faculty_nuid=faculty.nuid, section_id=section.section_id)
    )
    db_session.commit()

    assert client.delete(f"/faculty/{faculty.nuid}").status_code == 204
    assert db_session.get(Faculty, faculty.nuid) is None


def test_delete_faculty_not_found_returns_404(client, db_session):
    response = client.delete("/faculty/99999")
    assert response.status_code == 404
