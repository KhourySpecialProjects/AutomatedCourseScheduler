"""Tests for course router: GET /courses and GET /courses/{id}."""

from datetime import time

from app.core.enums import Campus, Semester
from app.models import Course, Schedule, Section, TimeBlock


def test_get_courses_empty(client, db_session):
    response = client.get("/courses")
    assert response.status_code == 200
    assert response.json() == []


def test_get_courses_returns_all(client, db_session):
    db_session.add_all(
        [
            Course(name="CS 2500", description="Fundamentals", credits=4),
            Course(name="CS 3200", description="DB Design", credits=4),
        ]
    )
    db_session.commit()

    response = client.get("/courses")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_courses_includes_section_count(client, db_session):
    course = Course(name="Algorithms", description="Algo", credits=4)
    db_session.add(course)
    db_session.flush()

    schedule = Schedule(name="F24", semester=Semester.FALL, year=2024)
    db_session.add(schedule)
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

    db_session.add_all(
        [
            Section(
                schedule_id=schedule.schedule_id,
                time_block_id=tb.time_block_id,
                course_id=course.course_id,
                section_number=1,
                capacity=30,
            ),
            Section(
                schedule_id=schedule.schedule_id,
                time_block_id=tb.time_block_id,
                course_id=course.course_id,
                section_number=2,
                capacity=25,
            ),
        ]
    )
    db_session.commit()

    response = client.get("/courses")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["SectionCount"] == 2
    assert data[0]["CourseName"] == "Algorithms"


def test_get_courses_filter_by_schedule_id(client, db_session):
    c1 = Course(name="CS 2500", description="A", credits=4)
    c2 = Course(name="CS 3200", description="B", credits=4)
    db_session.add_all([c1, c2])
    db_session.flush()

    s1 = Schedule(name="F24", semester=Semester.FALL, year=2024)
    s2 = Schedule(name="S25", semester=Semester.SPRING, year=2025)
    db_session.add_all([s1, s2])
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

    db_session.add(
        Section(
            schedule_id=s1.schedule_id,
            time_block_id=tb.time_block_id,
            course_id=c1.course_id,
            section_number=1,
            capacity=30,
        )
    )
    db_session.add(
        Section(
            schedule_id=s2.schedule_id,
            time_block_id=tb.time_block_id,
            course_id=c2.course_id,
            section_number=1,
            capacity=30,
        )
    )
    db_session.commit()

    response = client.get(f"/courses?schedule_id={s1.schedule_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["CourseName"] == "CS 2500"


def test_get_course_by_id(client, db_session):
    course = Course(name="OOD", description="Object-oriented", credits=4)
    db_session.add(course)
    db_session.commit()

    response = client.get(f"/courses/{course.course_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["CourseID"] == course.course_id
    assert data["CourseName"] == "OOD"
    assert data["CourseDescription"] == "Object-oriented"
    assert "SectionCount" in data


def test_get_course_not_found(client, db_session):
    response = client.get("/courses/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Course not found"
