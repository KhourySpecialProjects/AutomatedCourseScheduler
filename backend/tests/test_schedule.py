"""
Tests for schedule endpoints.

Endpoints covered:
  POST   /schedules                  — create a blank schedule shell
  GET    /schedules                  — list all, optional filters
  GET    /schedules/{id}             — get one by ID
  PUT    /schedules/{id}             — update name / complete flag
  DELETE /schedules/{id}             — soft delete

Sections endpoint (GET /schedules/{id}/sections) is tested in test_sections.py.
"""

from app.models import Schedule
from app.models.campus import Campus
from app.models.semester import Semester as SemesterModel


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


def _make_schedule(db, campus_id, semester_id, *, name="Test Schedule", complete=False):
    schedule = Schedule(
        name=name,
        semester_id=semester_id,
        campus=campus_id,
        complete=complete,
    )
    db.add(schedule)
    db.commit()
    return schedule


# ---------------------------------------------------------------------------
# POST /schedules — create
# ---------------------------------------------------------------------------


def test_create_schedule_returns_201(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    response = client.post(
        "/schedules",
        json={"name": "Fall 2024", "semester_id": semester.semester_id, "campus": campus.campus_id},
    )
    assert response.status_code == 201


def test_create_schedule_response_shape(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    response = client.post(
        "/schedules",
        json={"name": "Fall 2024", "semester_id": semester.semester_id, "campus": campus.campus_id},
    )
    data = response.json()
    expected_keys = {"schedule_id", "name", "semester_id", "draft", "campus", "complete", "active"}
    assert expected_keys.issubset(set(data.keys()))


def test_create_schedule_correct_values(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    response = client.post(
        "/schedules",
        json={"name": "My Schedule", "semester_id": semester.semester_id, "campus": campus.campus_id},
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
        json={"name": "Draft", "semester_id": semester.semester_id, "campus": campus.campus_id},
    )
    data = response.json()
    assert data["draft"] is True
    assert data["complete"] is False


def test_create_schedule_persisted_to_db(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    response = client.post(
        "/schedules",
        json={"name": "Persisted", "semester_id": semester.semester_id, "campus": campus.campus_id},
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
        json={"name": "ID Test", "semester_id": semester.semester_id, "campus": campus.campus_id},
    )
    schedule_id = response.json()["schedule_id"]
    assert isinstance(schedule_id, int)
    get_response = client.get(f"/schedules/{schedule_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "ID Test"


def test_create_multiple_schedules_same_campus(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    client.post("/schedules", json={"name": "S1", "semester_id": semester.semester_id, "campus": campus.campus_id})
    client.post("/schedules", json={"name": "S2", "semester_id": semester.semester_id, "campus": campus.campus_id})
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
    expected_keys = {"schedule_id", "name", "semester_id", "draft", "campus", "complete", "active"}
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
    assert data["complete"] is False
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
    response = client.get(f"/schedules?campus_id={campus_a.campus_id}&semester_id={semester.semester_id}")
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
    expected_keys = {"schedule_id", "name", "semester_id", "draft", "campus", "complete", "active"}
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


def test_update_schedule_complete_flag(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, semester.semester_id, complete=False)
    response = client.put(f"/schedules/{schedule.schedule_id}", json={"complete": True})
    assert response.status_code == 200
    assert response.json()["complete"] is True


def test_update_schedule_partial_name_preserves_complete(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, semester.semester_id, name="Original", complete=True)
    response = client.put(f"/schedules/{schedule.schedule_id}", json={"name": "Updated"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"
    assert data["complete"] is True


def test_update_schedule_partial_complete_preserves_name(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, semester.semester_id, name="Keep This Name", complete=False)
    response = client.put(f"/schedules/{schedule.schedule_id}", json={"complete": True})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Keep This Name"
    assert data["complete"] is True


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


def test_schedule_complete_defaults_to_false(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    _make_schedule(db_session, campus.campus_id, semester.semester_id)
    response = client.get("/schedules")
    assert response.json()[0]["complete"] is False


def test_multiple_schedules_same_campus(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    _make_schedule(db_session, campus.campus_id, semester.semester_id, name="S1")
    _make_schedule(db_session, campus.campus_id, semester.semester_id, name="S2")
    response = client.get(f"/schedules?campus_id={campus.campus_id}")
    assert len(response.json()) == 2