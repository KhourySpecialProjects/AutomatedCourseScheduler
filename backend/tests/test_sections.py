"""Tests for section router: GET /sections/{id} and GET /sections/{id}/rich."""

from datetime import time

from app.core.enums import Campus, Semester
from app.models import Course, Faculty, FacultyAssignment, Schedule, Section, TimeBlock


def test_get_sections_not_found_returns_404(client, db_session):
    response = client.get("/sections/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Schedule not found"


def test_get_rich_sections_not_found_returns_404(client, db_session):
    response = client.get("/sections/99999/rich")
    assert response.status_code == 404
    assert response.json()["detail"] == "Schedule not found"


def test_get_sections_empty(client, db_session):
    schedule = Schedule(name="Test", semester=Semester.FALL, year=2024)
    db_session.add(schedule)
    db_session.commit()

    response = client.get(f"/sections/{schedule.schedule_id}")
    assert response.status_code == 200
    assert response.json() == []


def test_get_sections_returns_flat_response(client, db_session):
    schedule = Schedule(name="Test", semester=Semester.FALL, year=2024)
    db_session.add(schedule)
    db_session.commit()

    course = Course(name="CS 2500", description="Desc", credits=4)
    db_session.add(course)
    db_session.flush()

    tb = TimeBlock(
        meetingDays="MW",
        start_time=time(10, 0),
        end_time=time(11, 0),
        timezone="EST",
        campus=Campus.BOSTON,
    )
    db_session.add(tb)
    db_session.flush()

    section = Section(
        schedule_id=schedule.schedule_id,
        time_block_id=tb.time_block_id,
        course_id=course.course_id,
        section_number=1,
        capacity=30,
    )
    db_session.add(section)
    db_session.commit()

    response = client.get(f"/sections/{schedule.schedule_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    sec = data[0]
    assert set(sec.keys()) == {
        "section_id",
        "schedule_id",
        "time_block_id",
        "course_id",
        "capacity",
        "section_number",
    }
    assert sec["section_id"] == section.section_id
    assert sec["capacity"] == 30


def test_get_rich_sections_returns_nested_data(client, db_session):
    schedule = Schedule(name="Test", semester=Semester.FALL, year=2024)
    db_session.add(schedule)
    db_session.commit()

    course = Course(name="Algorithms", description="Algo course", credits=4)
    db_session.add(course)
    db_session.flush()

    tb = TimeBlock(
        meetingDays="TR",
        start_time=time(9, 0),
        end_time=time(10, 0),
        timezone="EST",
        campus=Campus.BOSTON,
    )
    db_session.add(tb)
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

    section = Section(
        schedule_id=schedule.schedule_id,
        time_block_id=tb.time_block_id,
        course_id=course.course_id,
        section_number=2,
        capacity=40,
    )
    db_session.add(section)
    db_session.flush()

    db_session.add(
        FacultyAssignment(faculty_nuid=faculty.nuid, section_id=section.section_id)
    )
    db_session.commit()

    response = client.get(f"/sections/{schedule.schedule_id}/rich")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    sec = data[0]
    assert "course" in sec
    assert sec["course"]["name"] == "Algorithms"
    assert "time_block" in sec
    assert sec["time_block"]["days"] == "TR"
    assert "instructors" in sec
    assert len(sec["instructors"]) == 1
    assert sec["instructors"][0]["first_name"] == "John"
