"""Tests for schedule router: GET /schedules/{id} and GET /schedules/{id}/sections."""

from datetime import time

from app.core.enums import Campus, Semester
from app.models import (
    Course,
    Faculty,
    FacultyAssignment,
    Schedule,
    Section,
    TimeBlock,
)


def test_get_schedules_empty(client, db_session):
    response = client.get("/schedules")
    assert response.status_code == 200
    assert response.json() == []


def test_get_schedules_returns_all(client, db_session):
    db_session.add_all(
        [
            Schedule(name="Fall 2024", semester=Semester.FALL, year=2024),
            Schedule(name="Spring 2025", semester=Semester.SPRING, year=2025),
        ]
    )
    db_session.commit()

    response = client.get("/schedules")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_schedules_filter_by_semester_season(client, db_session):
    db_session.add_all(
        [
            Schedule(name="F24", semester=Semester.FALL, year=2024),
            Schedule(name="S25", semester=Semester.SPRING, year=2025),
            Schedule(name="F25", semester=Semester.FALL, year=2025),
        ]
    )
    db_session.commit()

    response = client.get("/schedules?semester_season=Fall")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(s["SemesterSeason"] == "Fall" for s in data)


def test_get_schedules_filter_by_year(client, db_session):
    db_session.add_all(
        [
            Schedule(name="A", semester=Semester.FALL, year=2024),
            Schedule(name="B", semester=Semester.SPRING, year=2025),
        ]
    )
    db_session.commit()

    response = client.get("/schedules?semester_year=2024")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["SemesterYear"] == 2024


def test_get_schedules_invalid_semester_season(client, db_session):
    response = client.get("/schedules?semester_season=Invalid")
    assert response.status_code == 422


def test_get_schedule_returns_metadata(client, db_session):
    schedule = Schedule(
        name="Fall 2024",
        semester=Semester.FALL,
        year=2024,
        draft=True,
    )
    db_session.add(schedule)
    db_session.commit()

    response = client.get(f"/schedules/{schedule.schedule_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["ScheduleID"] == schedule.schedule_id
    assert data["ScheduleName"] == "Fall 2024"
    assert data["SemesterSeason"] == "Fall"
    assert data["SemesterYear"] == 2024
    assert data["Complete"] is False


def test_get_schedule_not_found(client, db_session):
    response = client.get("/schedules/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Schedule not found"


def test_get_schedule_complete_status(client, db_session):
    schedule = Schedule(
        name="Spring 2025",
        semester=Semester.SPRING,
        year=2025,
        draft=False,
    )
    db_session.add(schedule)
    db_session.commit()

    response = client.get(f"/schedules/{schedule.schedule_id}")
    assert response.status_code == 200
    assert response.json()["Complete"] is True


def test_get_schedule_sections_empty(client, db_session):
    schedule = Schedule(name="Test", semester=Semester.FALL, year=2024)
    db_session.add(schedule)
    db_session.commit()

    response = client.get(f"/schedules/{schedule.schedule_id}/sections")
    assert response.status_code == 200
    assert response.json() == []


def test_get_schedule_sections_not_found(client, db_session):
    response = client.get("/schedules/99999/sections")
    assert response.status_code == 404
    assert response.json()["detail"] == "Schedule not found"


def test_get_schedule_sections_returns_rich_with_nested_course_faculty(
    client, db_session
):
    schedule = Schedule(name="Test", semester=Semester.FALL, year=2024)
    db_session.add(schedule)
    db_session.commit()

    course = Course(
        name="CS 2500",
        description="Fundamentals of CS",
        credits=4,
    )
    db_session.add(course)
    db_session.flush()

    time_block = TimeBlock(
        meetingDays="MW",
        start_time=time(10, 0),
        end_time=time(11, 0),
        timezone="EST",
        campus=Campus.BOSTON,
    )
    db_session.add(time_block)
    db_session.flush()

    faculty = Faculty(
        nuid=1001,
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        title="Professor",
        campus="Boston",
    )
    db_session.add(faculty)
    db_session.flush()

    section = Section(
        schedule_id=schedule.schedule_id,
        time_block_id=time_block.time_block_id,
        course_id=course.course_id,
        section_number=1,
        capacity=30,
    )
    db_session.add(section)
    db_session.flush()

    db_session.add(
        FacultyAssignment(
            faculty_nuid=faculty.nuid,
            section_id=section.section_id,
        )
    )
    db_session.commit()

    response = client.get(f"/schedules/{schedule.schedule_id}/sections")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    sec = data[0]
    assert sec["section_id"] == section.section_id
    assert sec["section_number"] == 1
    assert sec["capacity"] == 30
    assert sec["schedule_id"] == schedule.schedule_id
    assert "course" in sec
    assert sec["course"]["course_id"] == course.course_id
    assert sec["course"]["name"] == "CS 2500"
    assert sec["course"]["description"] == "Fundamentals of CS"
    assert sec["course"]["credits"] == 4
    assert "time_block" in sec
    assert sec["time_block"]["time_block_id"] == time_block.time_block_id
    assert sec["time_block"]["days"] == "MW"
    assert "instructors" in sec
    assert len(sec["instructors"]) == 1
    inst = sec["instructors"][0]
    assert inst["nuid"] == 1001
    assert inst["first_name"] == "Jane"
    assert inst["last_name"] == "Doe"
    assert inst["title"] == "Professor"
    assert inst["email"] == "jane@example.com"
    assert "course_preferences" in inst
    assert "meeting_preferences" in inst


def test_get_schedule_sections_multiple(client, db_session):
    schedule = Schedule(name="Test", semester=Semester.FALL, year=2024)
    db_session.add(schedule)
    db_session.commit()

    course = Course(name="CS 2500", description="Desc", credits=4)
    db_session.add(course)
    db_session.flush()

    tb = TimeBlock(
        meetingDays="TR",
        start_time=time(10, 0),
        end_time=time(11, 0),
        timezone="EST",
        campus=Campus.BOSTON,
    )
    db_session.add(tb)
    db_session.flush()

    for i in range(3):
        db_session.add(
            Section(
                schedule_id=schedule.schedule_id,
                time_block_id=tb.time_block_id,
                course_id=course.course_id,
                section_number=i + 1,
                capacity=25,
            )
        )
    db_session.commit()

    response = client.get(f"/schedules/{schedule.schedule_id}/sections")
    assert response.status_code == 200
    assert len(response.json()) == 3
