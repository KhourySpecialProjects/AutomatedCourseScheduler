"""
Tests for schedule endpoints.

Endpoints covered:
  POST   /schedules                  — create a blank schedule shell
  GET    /schedules                  — list all, optional filters
  GET    /schedules/{id}             — get one by ID
  PUT    /schedules/{id}             — update name / draft flag
  DELETE /schedules/{id}             — soft delete
  GET    /schedules/{id}/locks       — get all active locks for a schedule

Sections endpoint (GET /schedules/{id}/sections) is tested in test_sections.py.
"""

from datetime import datetime, time, timedelta

from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.core.auth import get_db_user
from app.main import app
from app.models import Schedule, TimeBlock
from app.models.campus import Campus
from app.models.course import Course as CourseModel
from app.models.section import Section as SectionModel
from app.models.section_lock import SectionLock
from app.models.semester import Semester as SemesterModel
from app.models.user import User

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_campus(db, name="Boston"):
    campus = Campus(name=name)
    db.add(campus)
    db.flush()
    return campus


def _make_semester(db, season="Fall", year=2024):
    semester = SemesterModel(season=season, year=year)
    db.add(semester)
    db.flush()
    return semester


def _make_schedule(db, campus_id, semester_id, *, name="Test Schedule"):
    schedule = Schedule(
        name=name,
        semester_id=semester_id,
        campus=campus_id,
    )
    db.add(schedule)
    db.commit()
    return schedule


def _make_user(db, nuid):
    user = User(
        nuid=nuid,
        first_name="Test",
        last_name="User",
        email=f"user{nuid}@example.com",
        role="ADMIN",
    )
    db.add(user)
    db.commit()
    return user


def _make_course(
    db, subject="CS", code=1800, name="CS 1800", description="Discrete Structures", credits=4
):
    course = CourseModel(
        subject=subject, code=code, name=name, description=description, credits=credits
    )
    db.add(course)
    db.flush()
    return course


def _make_time_block(db, campus_id):
    tb = TimeBlock(
        meeting_days="MWF",
        start_time=time(9, 0),
        end_time=time(10, 0),
        campus=campus_id,
    )
    db.add(tb)
    db.flush()
    return tb


def _make_section(db, schedule_id, course_id, time_block_id):
    section = SectionModel(
        section_number=1,
        capacity=30,
        schedule_id=schedule_id,
        course_id=course_id,
        time_block_id=time_block_id,
    )
    db.add(section)
    db.flush()
    return section


def _make_historical_context(db, campus, season="Fall", current_year=2024):
    """Create a previous-year semester with a schedule and one course section.

    This is the historical data that ``generate_course_list`` pulls from when
    building the course list for a newly created schedule.  Returns the Course
    that was added to the historical schedule.
    """
    prev_semester = SemesterModel(season=season, year=current_year - 1)
    db.add(prev_semester)
    db.flush()
    prev_schedule = Schedule(
        name="Prev Year Schedule",
        semester_id=prev_semester.semester_id,
        campus=campus.campus_id,
    )
    db.add(prev_schedule)
    db.flush()
    course = _make_course(db)
    time_block = _make_time_block(db, campus.campus_id)
    _make_section(db, prev_schedule.schedule_id, course.course_id, time_block.time_block_id)
    db.commit()
    return course


# ---------------------------------------------------------------------------
# POST /schedules — create
# ---------------------------------------------------------------------------


def test_create_schedule_returns_201(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    response = client.post(
        "/schedules",
        json={
            "name": "Fall 2024",
            "semester_id": semester.semester_id,
            "campus": campus.campus_id,
        },
    )
    assert response.status_code == 201


def test_create_schedule_response_shape(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    response = client.post(
        "/schedules",
        json={
            "name": "Fall 2024",
            "semester_id": semester.semester_id,
            "campus": campus.campus_id,
        },
    )
    data = response.json()
    expected_keys = {
        "schedule_id",
        "name",
        "semester_id",
        "draft",
        "campus",
        "active",
        "course_list",
    }
    assert expected_keys.issubset(set(data.keys()))


def test_create_schedule_correct_values(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    response = client.post(
        "/schedules",
        json={
            "name": "My Schedule",
            "semester_id": semester.semester_id,
            "campus": campus.campus_id,
        },
    )
    data = response.json()
    assert data["name"] == "My Schedule"
    assert data["campus"] == campus.campus_id
    assert data["semester_id"] == semester.semester_id


def test_create_schedule_defaults(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    response = client.post(
        "/schedules",
        json={
            "name": "Draft",
            "semester_id": semester.semester_id,
            "campus": campus.campus_id,
        },
    )
    data = response.json()
    assert data["draft"] is True
    assert data["course_list"] == []


def test_create_schedule_persisted_to_db(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    response = client.post(
        "/schedules",
        json={
            "name": "Persisted",
            "semester_id": semester.semester_id,
            "campus": campus.campus_id,
        },
    )
    schedule_id = response.json()["schedule_id"]
    db_session.expire_all()
    found = db_session.get(Schedule, schedule_id)
    assert found is not None
    assert found.name == "Persisted"


def test_create_schedule_returns_id(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    response = client.post(
        "/schedules",
        json={
            "name": "ID Test",
            "semester_id": semester.semester_id,
            "campus": campus.campus_id,
        },
    )
    schedule_id = response.json()["schedule_id"]
    assert isinstance(schedule_id, int)
    get_response = client.get(f"/schedules/{schedule_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "ID Test"


def test_create_schedule_course_list_populated_from_history(client, db_session):
    """Courses from the previous year's schedule appear in the new
    schedule's course_list."""
    campus = _make_campus(db_session)
    semester = _make_semester(db_session, season="Fall", year=2024)
    historical_course = _make_historical_context(
        db_session, campus, season="Fall", current_year=2024
    )
    response = client.post(
        "/schedules",
        json={
            "name": "Fall 2024",
            "semester_id": semester.semester_id,
            "campus": campus.campus_id,
        },
    )
    assert response.status_code == 201
    course_list = response.json()["course_list"]
    assert len(course_list) == 1
    assert course_list[0]["course_id"] == historical_course.course_id


def test_create_schedule_course_list_item_fields(client, db_session):
    """Each item in course_list contains all required CourseResponse fields."""
    campus = _make_campus(db_session)
    semester = _make_semester(db_session, season="Fall", year=2024)
    _make_historical_context(db_session, campus, season="Fall", current_year=2024)
    response = client.post(
        "/schedules",
        json={
            "name": "Fall 2024",
            "semester_id": semester.semester_id,
            "campus": campus.campus_id,
        },
    )
    item = response.json()["course_list"][0]
    expected_keys = {
        "course_id",
        "subject",
        "code",
        "name",
        "description",
        "section_count",
        "priority",
        "qualified_faculty",
    }
    assert expected_keys.issubset(set(item.keys()))


def test_create_schedule_course_list_item_correct_values(client, db_session):
    """course_list items carry the correct name, subject, number, and section count."""
    campus = _make_campus(db_session)
    semester = _make_semester(db_session, season="Fall", year=2024)
    historical_course = _make_historical_context(
        db_session, campus, season="Fall", current_year=2024
    )
    response = client.post(
        "/schedules",
        json={
            "name": "Fall 2024",
            "semester_id": semester.semester_id,
            "campus": campus.campus_id,
        },
    )
    item = response.json()["course_list"][0]
    assert item["course_id"] == historical_course.course_id
    assert item["subject"] == "CS"
    assert item["code"] == 1800
    assert item["name"] == historical_course.name  # "CS 1800"
    assert item["section_count"] == 1  # one section in the historical schedule


def test_create_schedule_course_list_includes_new_courses(client, db_session):
    """Courses passed via new_courses are appended to course_list."""
    campus = _make_campus(db_session)
    semester = _make_semester(db_session, season="Fall", year=2024)
    _make_historical_context(db_session, campus, season="Fall", current_year=2024)
    new_course = _make_course(
        db_session, name="CS 3800", description="Theory of Computation", credits=4
    )
    db_session.commit()
    response = client.post(
        "/schedules",
        json={
            "name": "Fall 2024",
            "semester_id": semester.semester_id,
            "campus": campus.campus_id,
            "new_courses": [new_course.course_id],
        },
    )
    assert response.status_code == 201
    course_ids = [c["course_id"] for c in response.json()["course_list"]]
    assert new_course.course_id in course_ids


def test_create_schedule_new_courses_section_count_is_one(client, db_session):
    """Courses added via new_courses always have section_count == 1."""
    campus = _make_campus(db_session)
    semester = _make_semester(db_session, season="Fall", year=2024)
    _make_historical_context(db_session, campus, season="Fall", current_year=2024)
    new_course = _make_course(
        db_session, name="CS 3800", description="Theory of Computation", credits=4
    )
    db_session.commit()
    response = client.post(
        "/schedules",
        json={
            "name": "Fall 2024",
            "semester_id": semester.semester_id,
            "campus": campus.campus_id,
            "new_courses": [new_course.course_id],
        },
    )
    course_list = response.json()["course_list"]
    new_entry = next(c for c in course_list if c["course_id"] == new_course.course_id)
    assert new_entry["section_count"] == 1


def test_create_multiple_schedules_same_campus(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    client.post(
        "/schedules",
        json={
            "name": "S1",
            "semester_id": semester.semester_id,
            "campus": campus.campus_id,
        },
    )
    client.post(
        "/schedules",
        json={
            "name": "S2",
            "semester_id": semester.semester_id,
            "campus": campus.campus_id,
        },
    )
    response = client.get("/schedules")
    assert len(response.json()) == 2


# ---------------------------------------------------------------------------
# GET /schedules — list all
# ---------------------------------------------------------------------------


def test_get_schedules_empty(client, db_session):
    response = client.get("/schedules")
    assert response.status_code == 200
    assert response.json() == []


def test_get_schedules_returns_all(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    _make_schedule(db_session, campus.campus_id, semester.semester_id, name="S1")
    _make_schedule(db_session, campus.campus_id, semester.semester_id, name="S2")
    response = client.get("/schedules")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_schedules_response_shape(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    _make_schedule(db_session, campus.campus_id, semester.semester_id)
    response = client.get("/schedules")
    data = response.json()[0]
    expected_keys = {
        "schedule_id",
        "name",
        "semester_id",
        "draft",
        "campus",
        "active",
    }
    assert expected_keys.issubset(set(data.keys()))


def test_get_schedules_correct_values(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, semester.semester_id, name="Fall 2024")
    response = client.get("/schedules")
    data = response.json()[0]
    assert data["schedule_id"] == schedule.schedule_id
    assert data["name"] == "Fall 2024"
    assert data["campus"] == campus.campus_id
    assert data["semester_id"] == semester.semester_id
    assert data["draft"] is True


def test_get_schedules_filter_by_campus_id(client, db_session):
    campus_a = _make_campus(db_session, "Boston")
    campus_b = _make_campus(db_session, "Oakland")
    semester = _make_semester(db_session)
    _make_schedule(db_session, campus_a.campus_id, semester.semester_id, name="Boston Schedule")
    _make_schedule(db_session, campus_b.campus_id, semester.semester_id, name="Oakland Schedule")
    response = client.get(f"/schedules?campus_id={campus_a.campus_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Boston Schedule"


def test_get_schedules_filter_by_semester_id(client, db_session):
    campus = _make_campus(db_session)
    semester_a = _make_semester(db_session, season="Fall", year=2024)
    semester_b = _make_semester(db_session, season="Spring", year=2025)
    _make_schedule(db_session, campus.campus_id, semester_a.semester_id, name="Fall")
    _make_schedule(db_session, campus.campus_id, semester_b.semester_id, name="Spring")
    response = client.get(f"/schedules?semester_id={semester_a.semester_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Fall"


def test_get_schedules_filter_multiple_params(client, db_session):
    campus_a = _make_campus(db_session, "Boston")
    campus_b = _make_campus(db_session, "Oakland")
    semester = _make_semester(db_session)
    _make_schedule(db_session, campus_a.campus_id, semester.semester_id, name="Match")
    _make_schedule(db_session, campus_b.campus_id, semester.semester_id, name="Wrong Campus")
    response = client.get(
        f"/schedules?campus_id={campus_a.campus_id}&semester_id={semester.semester_id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Match"


def test_get_schedules_filter_no_match_returns_empty(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    _make_schedule(db_session, campus.campus_id, semester.semester_id)
    response = client.get("/schedules?semester_id=99999")
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# GET /schedules/{id} — get one
# ---------------------------------------------------------------------------


def test_get_schedule_by_id(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, semester.semester_id, name="Fall 2024")
    response = client.get(f"/schedules/{schedule.schedule_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Fall 2024"
    assert response.json()["schedule_id"] == schedule.schedule_id


def test_get_schedule_by_id_not_found(client, db_session):
    response = client.get("/schedules/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_schedule_by_id_response_shape(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, semester.semester_id)
    response = client.get(f"/schedules/{schedule.schedule_id}")
    data = response.json()
    expected_keys = {
        "schedule_id",
        "name",
        "semester_id",
        "draft",
        "campus",
        "active",
    }
    assert expected_keys.issubset(set(data.keys()))


def test_get_schedule_by_id_campus_is_int(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, semester.semester_id)
    response = client.get(f"/schedules/{schedule.schedule_id}")
    assert isinstance(response.json()["campus"], int)
    assert response.json()["campus"] == campus.campus_id


# ---------------------------------------------------------------------------
# PUT /schedules/{id} — update
# ---------------------------------------------------------------------------


def test_update_schedule_name(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, semester.semester_id, name="Old Name")
    response = client.put(f"/schedules/{schedule.schedule_id}", json={"name": "New Name"})
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


def test_update_schedule_empty_put(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, semester.semester_id)
    response = client.put(f"/schedules/{schedule.schedule_id}")
    assert response.status_code == 200


def test_update_schedule_partial_name(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(
        db_session,
        campus.campus_id,
        semester.semester_id,
        name="Original",
    )
    response = client.put(f"/schedules/{schedule.schedule_id}", json={"name": "Updated"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"


def test_update_schedule_no_body_preserves_name(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(
        db_session,
        campus.campus_id,
        semester.semester_id,
        name="Keep This Name",
    )
    response = client.put(f"/schedules/{schedule.schedule_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Keep This Name"


def test_update_schedule_persisted_to_db(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, semester.semester_id, name="Before")
    client.put(f"/schedules/{schedule.schedule_id}", json={"name": "After"})
    db_session.expire_all()
    updated = db_session.get(Schedule, schedule.schedule_id)
    assert updated.name == "After"


def test_update_schedule_not_found(client, db_session):
    response = client.put("/schedules/99999", json={"name": "Ghost"})
    assert response.status_code == 404


def test_update_schedule_empty_body(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, semester.semester_id, name="Unchanged")
    response = client.put(f"/schedules/{schedule.schedule_id}", json={})
    assert response.status_code == 200
    assert response.json()["name"] == "Unchanged"


def test_update_schedule_immutable_fields_ignored(client, db_session):
    """Fields not in ScheduleUpdate (semester_id, campus) are stripped by Pydantic."""
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, semester.semester_id)
    response = client.put(
        f"/schedules/{schedule.schedule_id}",
        json={"semester_id": 9999, "name": "Updated"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["semester_id"] == semester.semester_id
    assert data["name"] == "Updated"


# ---------------------------------------------------------------------------
# DELETE /schedules/{id}
# ---------------------------------------------------------------------------


def test_delete_schedule(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, semester.semester_id)
    schedule_id = schedule.schedule_id
    response = client.delete(f"/schedules/{schedule_id}")
    assert response.status_code == 204
    db_session.expire_all()
    row = db_session.get(Schedule, schedule_id)
    assert row is not None
    assert row.active is False


def test_delete_schedule_not_found(client, db_session):
    response = client.delete("/schedules/99999")
    assert response.status_code == 404


def test_delete_schedule_no_response_body(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, semester.semester_id)
    response = client.delete(f"/schedules/{schedule.schedule_id}")
    assert response.status_code == 204
    assert response.content == b""


def test_delete_schedule_second_attempt_returns_404(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, semester.semester_id)
    schedule_id = schedule.schedule_id
    client.delete(f"/schedules/{schedule_id}")
    response = client.delete(f"/schedules/{schedule_id}")
    assert response.status_code == 404


def test_delete_schedule_no_longer_in_list(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, semester.semester_id)
    schedule_id = schedule.schedule_id
    client.delete(f"/schedules/{schedule_id}")
    response = client.get("/schedules")
    ids = [s["schedule_id"] for s in response.json()]
    assert schedule_id not in ids


# ---------------------------------------------------------------------------
# Default value tests
# ---------------------------------------------------------------------------


def test_schedule_draft_defaults_to_true(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    _make_schedule(db_session, campus.campus_id, semester.semester_id)
    response = client.get("/schedules")
    assert response.json()[0]["draft"] is True


def test_multiple_schedules_same_campus(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    _make_schedule(db_session, campus.campus_id, semester.semester_id, name="S1")
    _make_schedule(db_session, campus.campus_id, semester.semester_id, name="S2")
    response = client.get(f"/schedules?campus_id={campus.campus_id}")
    assert len(response.json()) == 2


# ---------------------------------------------------------------------------
# GET /schedules/{id}/locks
# ---------------------------------------------------------------------------


def test_get_schedule_locks_empty(client: TestClient, db_session: Session) -> None:
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, semester.semester_id)

    response = client.get(f"/schedules/{schedule.schedule_id}/locks")

    assert response.json() == []


def test_get_schedule_locks_non_empty(client: TestClient, db_session: Session) -> None:
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, semester.semester_id)
    user = _make_user(db_session, nuid=1)
    course = _make_course(db_session)
    time_block = _make_time_block(db_session, campus.campus_id)
    section = _make_section(
        db_session, schedule.schedule_id, course.course_id, time_block.time_block_id
    )

    app.dependency_overrides[get_db_user] = lambda: user
    client.post(f"/sections/{section.section_id}/lock")
    response = client.get(f"/schedules/{schedule.schedule_id}/locks")

    assert len(response.json()) == 1
    data = response.json()[0]
    assert data["section_id"] == section.section_id
    assert data["locked_by"] == user.user_id
    assert data["display_name"] == "Test User"
    assert "expires_at" in data


def test_get_schedule_locks_returns_active(client: TestClient, db_session: Session) -> None:
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, semester.semester_id)
    user1 = _make_user(db_session, nuid=1)
    user2 = _make_user(db_session, nuid=2)
    user3 = _make_user(db_session, nuid=3)
    course = _make_course(db_session)
    time_block = _make_time_block(db_session, campus.campus_id)
    section1 = _make_section(
        db_session, schedule.schedule_id, course.course_id, time_block.time_block_id
    )
    section2 = _make_section(
        db_session, schedule.schedule_id, course.course_id, time_block.time_block_id
    )
    section3 = _make_section(
        db_session, schedule.schedule_id, course.course_id, time_block.time_block_id
    )

    # two active locks
    app.dependency_overrides[get_db_user] = lambda: user1
    client.post(f"/sections/{section1.section_id}/lock")
    app.dependency_overrides[get_db_user] = lambda: user2
    client.post(f"/sections/{section2.section_id}/lock")

    # one expired lock inserted directly
    expired_lock = SectionLock(
        section_id=section3.section_id,
        locked_by=user3.user_id,
        expires_at=datetime.now() - timedelta(minutes=10),
    )
    db_session.add(expired_lock)
    db_session.commit()

    response = client.get(f"/schedules/{schedule.schedule_id}/locks")

    assert len(response.json()) == 2
    locked_by_ids = {lock["locked_by"] for lock in response.json()}
    assert user1.user_id in locked_by_ids
    assert user2.user_id in locked_by_ids
    assert user3.user_id not in locked_by_ids


def test_get_schedule_locks_excludes_other_schedules(
    client: TestClient, db_session: Session
) -> None:
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule1 = _make_schedule(db_session, campus.campus_id, semester.semester_id, name="S1")
    schedule2 = _make_schedule(db_session, campus.campus_id, semester.semester_id, name="S2")
    user = _make_user(db_session, nuid=1)
    course = _make_course(db_session)
    time_block = _make_time_block(db_session, campus.campus_id)
    section = _make_section(
        db_session, schedule1.schedule_id, course.course_id, time_block.time_block_id
    )

    app.dependency_overrides[get_db_user] = lambda: user
    client.post(f"/sections/{section.section_id}/lock")
    response = client.get(f"/schedules/{schedule2.schedule_id}/locks")

    assert response.json() == []
