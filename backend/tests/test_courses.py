"""Tests for course router: GET /courses and GET /courses/{id}."""

from datetime import time

from app.models import Course, Schedule, Section, TimeBlock
from app.models.campus import Campus as CampusModel
from app.models.semester import Semester as SemesterModel

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_campus(db, name="Boston"):
    campus = CampusModel(name=name)
    db.add(campus)
    db.flush()
    return campus


def _make_semester(db, season="Fall", year=2024):
    semester = SemesterModel(season=season, year=year)
    db.add(semester)
    db.flush()
    return semester


def _make_time_block(db, campus_id):
    tb = TimeBlock(
        meeting_days="MW",
        start_time=time(10, 0),
        end_time=time(11, 0),
        campus=campus_id,
    )
    db.add(tb)
    db.flush()
    return tb


# ---------------------------------------------------------------------------
# GET /courses
# ---------------------------------------------------------------------------


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
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)

    course = Course(name="Algorithms", description="Algo", credits=4)
    db_session.add(course)
    db_session.flush()

    schedule = Schedule(
        name="F24", semester_id=semester.semester_id, campus=campus.campus_id
    )
    db_session.add(schedule)
    db_session.flush()

    tb = _make_time_block(db_session, campus.campus_id)

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

    response = client.get("/courses?schedule_id=99999")
    assert response.status_code == 400
    assert response.json()["detail"] == "ScheduleID is invalid"


def test_get_courses_filter_by_schedule_id(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)

    c1 = Course(name="CS 2500", description="A", credits=4)
    c2 = Course(name="CS 3200", description="B", credits=4)
    db_session.add_all([c1, c2])
    db_session.flush()

    s1 = Schedule(name="F24", semester_id=semester.semester_id, campus=campus.campus_id)
    s2 = Schedule(name="S25", semester_id=semester.semester_id, campus=campus.campus_id)
    db_session.add_all([s1, s2])
    db_session.flush()

    tb = _make_time_block(db_session, campus.campus_id)

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


# ---------------------------------------------------------------------------
# GET /courses/{course_id}
# ---------------------------------------------------------------------------


def test_get_course_by_id_invalid_schedule_id_returns_400(client, db_session):
    course = Course(name="OOD", description="Object-oriented", credits=4)
    db_session.add(course)
    db_session.commit()
    response = client.get(f"/courses/{course.course_id}?schedule_id=99999")
    assert response.status_code == 400
    assert response.json()["detail"] == "ScheduleID is invalid"


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


def test_create_course_success(client, db_session):
    response = client.post(
        "/courses",
        json={
            "name": "CS 1800",
            "description": "Discrete structures",
            "credits": 4,
            "priority": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["CourseName"] == "CS 1800"
    assert data["CourseDescription"] == "Discrete structures"
    assert data["Priority"] is True
    assert data["SectionCount"] == 0
    assert "CourseID" in data


def test_patch_course_success(client, db_session):
    course = Course(name="CS 2500", description="Was old", credits=4, priority=True)
    db_session.add(course)
    db_session.commit()

    response = client.patch(
        f"/courses/{course.course_id}",
        json={"name": "CS 2510", "credits": 3, "priority": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["CourseName"] == "CS 2510"
    assert data["CourseDescription"] == "Was old"
    assert data["CourseID"] == course.course_id
    db_session.expire_all()
    reloaded = db_session.get(Course, course.course_id)
    assert reloaded is not None
    assert reloaded.credits == 3
    assert reloaded.priority is False


def test_patch_course_priority_null_returns_400(client, db_session):
    course = Course(name="CS 2600", description="X", credits=4, priority=False)
    db_session.add(course)
    db_session.commit()

    response = client.patch(
        f"/courses/{course.course_id}",
        json={"priority": None},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Priority is invalid"


def test_patch_course_not_found_returns_404(client, db_session):
    response = client.patch("/courses/99999", json={"name": "X"})
    assert response.status_code == 404


def test_patch_course_invalid_credits_returns_400(client, db_session):
    course = Course(name="X", description="Y", credits=4)
    db_session.add(course)
    db_session.commit()

    response = client.patch(
        f"/courses/{course.course_id}",
        json={"credits": -1},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Credits is invalid"


def test_delete_course_success(client, db_session):
    course = Course(name="To go", description="Bye", credits=1)
    db_session.add(course)
    db_session.commit()

    response = client.delete(f"/courses/{course.course_id}")
    assert response.status_code == 204
    assert db_session.get(Course, course.course_id) is None


def test_delete_course_not_found_returns_404(client, db_session):
    response = client.delete("/courses/99999")
    assert response.status_code == 404


def test_delete_course_with_sections_returns_400(client, db_session):
    course = Course(name="Busy", description="Has sections", credits=4)
    db_session.add(course)
    db_session.flush()
    schedule = Schedule(name="F24", semester=Semester.FALL, year=2024)
    db_session.add(schedule)
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
        Section(
            schedule_id=schedule.schedule_id,
            time_block_id=tb.time_block_id,
            course_id=course.course_id,
            section_number=1,
            capacity=30,
        )
    )
    db_session.commit()

    response = client.delete(f"/courses/{course.course_id}")
    assert response.status_code == 400
    assert response.json()["detail"] == "Course has sections and cannot be deleted"
