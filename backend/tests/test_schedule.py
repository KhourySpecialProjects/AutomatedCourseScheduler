"""
Tests for schedule endpoints. (From Claude)

Endpoints covered:
  POST   /schedules                  — create a blank schedule shell
  GET    /schedules                  — list all, optional filters
  GET    /schedules/{id}             — get one by ID
  PUT    /schedules/{id}             — update name / complete flag
  DELETE /schedules/{id}             — hard delete

Endpoints NOT tested (stubbed 501):
  GET    /schedules/{id}/export/csv  — not implemented yet

Sections endpoint (GET /schedules/{id}/sections) is tested in test_sections.py.

Test structure:
  - Each test inserts only what it needs via helper fixtures
  - _make_campus / _make_schedule helpers keep fixtures DRY
  - Tests are grouped by endpoint with clear comments
  - Covers: happy paths, 404s, filters, partial updates,
    field immutability, boundary values, null handling,
    persistence checks, and default field values
"""

from app.core.enums import Semester
from app.models import Schedule
from app.models.campus import Campus

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_campus(db, name="Boston"):
    """Insert a Campus row and flush so campus_id is available."""
    campus = Campus(name=name)
    db.add(campus)
    db.flush()
    return campus


def _make_schedule(
    db,
    campus_id,
    *,
    name="Test Schedule",
    semester=Semester.FALL,
    year=2024,
    complete=False,
):
    """Insert a Schedule row and commit so schedule_id is available."""
    schedule = Schedule(
        name=name,
        semester=semester,
        year=year,
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
    """
    Creating a schedule returns HTTP 201 Created.
    """
    campus = _make_campus(db_session)
    response = client.post(
        "/schedules",
        json={
            "name": "Fall 2024",
            "semester": "Fall",
            "year": 2024,
            "campus": campus.campus_id,
        },
    )
    assert response.status_code == 201


def test_create_schedule_response_shape(client, db_session):
    """
    Created schedule has all expected fields in the response.
    Guards against schema omissions on create vs read.
    """
    campus = _make_campus(db_session)
    response = client.post(
        "/schedules",
        json={
            "name": "Fall 2024",
            "semester": "Fall",
            "year": 2024,
            "campus": campus.campus_id,
        },
    )
    data = response.json()
    expected_keys = {
        "schedule_id",
        "name",
        "semester",
        "year",
        "draft",
        "campus",
        "complete",
    }
    assert expected_keys.issubset(set(data.keys()))


def test_create_schedule_correct_values(client, db_session):
    """
    Created schedule response reflects the values that were sent.
    """
    campus = _make_campus(db_session)
    response = client.post(
        "/schedules",
        json={
            "name": "My Schedule",
            "semester": "Fall",
            "year": 2025,
            "campus": campus.campus_id,
        },
    )
    data = response.json()
    assert data["name"] == "My Schedule"
    assert data["year"] == 2025
    assert data["campus"] == campus.campus_id


def test_create_schedule_defaults(client, db_session):
    """
    A newly created schedule has draft=True and complete=False by default.
    This reflects the intended workflow — schedules start as blank drafts,
    complete only after the algorithm runs and a user finalizes the schedule.
    """
    campus = _make_campus(db_session)
    response = client.post(
        "/schedules",
        json={
            "name": "Draft",
            "semester": "Fall",
            "year": 2024,
            "campus": campus.campus_id,
        },
    )
    data = response.json()
    assert data["draft"] is True
    assert data["complete"] is False


def test_create_schedule_persisted_to_db(client, db_session):
    """
    After creation the schedule exists in the database.
    Guards against a service that returns a response without actually writing.
    """
    campus = _make_campus(db_session)
    response = client.post(
        "/schedules",
        json={
            "name": "Persisted",
            "semester": "Fall",
            "year": 2024,
            "campus": campus.campus_id,
        },
    )
    schedule_id = response.json()["schedule_id"]

    db_session.expire_all()
    found = db_session.get(Schedule, schedule_id)
    assert found is not None
    assert found.name == "Persisted"


def test_create_schedule_returns_id(client, db_session):
    """
    The response includes a schedule_id that can be used to look up the schedule.
    """
    campus = _make_campus(db_session)
    response = client.post(
        "/schedules",
        json={
            "name": "ID Test",
            "semester": "Fall",
            "year": 2024,
            "campus": campus.campus_id,
        },
    )
    schedule_id = response.json()["schedule_id"]
    assert isinstance(schedule_id, int)

    get_response = client.get(f"/schedules/{schedule_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "ID Test"


def test_create_multiple_schedules_same_campus(client, db_session):
    """
    Multiple schedules can be created for the same campus.
    No unique constraint on campus — a campus can have many schedules
    across different semesters and years.
    """
    campus = _make_campus(db_session)
    client.post(
        "/schedules",
        json={
            "name": "Fall 2024",
            "semester": "Fall",
            "year": 2024,
            "campus": campus.campus_id,
        },
    )
    client.post(
        "/schedules",
        json={
            "name": "Spring 2025",
            "semester": "Spring",
            "year": 2025,
            "campus": campus.campus_id,
        },
    )

    response = client.get("/schedules")
    assert len(response.json()) == 2


# ---------------------------------------------------------------------------
# GET /schedules — list all
# ---------------------------------------------------------------------------


def test_get_schedules_empty(client, db_session):
    """
    When no schedules exist the endpoint returns 200 with an empty list.
    Verifies the endpoint doesn't 500 on an empty table.
    """
    response = client.get("/schedules")
    assert response.status_code == 200
    assert response.json() == []


def test_get_schedules_returns_all(client, db_session):
    """
    When multiple schedules exist all are returned.
    Verifies the repository isn't limiting results unexpectedly.
    """
    campus = _make_campus(db_session)
    _make_schedule(db_session, campus.campus_id, name="Fall 2024")
    _make_schedule(
        db_session,
        campus.campus_id,
        name="Spring 2025",
        semester=Semester.SPRING,
        year=2025,
    )

    response = client.get("/schedules")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_schedules_response_shape(client, db_session):
    """
    Each schedule object has all required fields.
    Guards against schema field renames or omissions silently breaking the response.
    """
    campus = _make_campus(db_session)
    _make_schedule(db_session, campus.campus_id)

    response = client.get("/schedules")
    data = response.json()[0]
    expected_keys = {
        "schedule_id",
        "name",
        "semester",
        "year",
        "draft",
        "campus",
        "complete",
    }
    assert expected_keys.issubset(set(data.keys()))


def test_get_schedules_correct_values(client, db_session):
    """
    The returned data matches what was inserted.
    Catches serialization bugs where values are returned but wrong.
    """
    campus = _make_campus(db_session)
    schedule = _make_schedule(
        db_session,
        campus.campus_id,
        name="Fall 2024",
        semester=Semester.FALL,
        year=2024,
    )

    response = client.get("/schedules")
    data = response.json()[0]
    assert data["schedule_id"] == schedule.schedule_id
    assert data["name"] == "Fall 2024"
    assert data["year"] == 2024
    assert data["campus"] == campus.campus_id
    assert data["complete"] is False
    assert data["draft"] is True


def test_get_schedules_filter_by_campus_id(client, db_session):
    """
    ?campus_id= only returns schedules for that campus.
    Verifies the campus filter is wired through router → service → repository correctly.
    """
    campus_a = _make_campus(db_session, "Boston")
    campus_b = _make_campus(db_session, "Oakland")
    _make_schedule(db_session, campus_a.campus_id, name="Boston Schedule")
    _make_schedule(db_session, campus_b.campus_id, name="Oakland Schedule")

    response = client.get(f"/schedules?campus_id={campus_a.campus_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Boston Schedule"


def test_get_schedules_filter_by_semester(client, db_session):
    """
    ?semester_season= only returns schedules for that semester.
    Verifies semester string filtering works end to end.
    """
    campus = _make_campus(db_session)
    _make_schedule(db_session, campus.campus_id, name="Fall", semester=Semester.FALL)
    _make_schedule(
        db_session, campus.campus_id, name="Spring", semester=Semester.SPRING
    )

    response = client.get("/schedules?semester_season=Fall")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Fall"


def test_get_schedules_filter_by_year(client, db_session):
    """
    ?semester_year= only returns schedules for that year.
    """
    campus = _make_campus(db_session)
    _make_schedule(db_session, campus.campus_id, name="2024", year=2024)
    _make_schedule(db_session, campus.campus_id, name="2025", year=2025)

    response = client.get("/schedules?semester_year=2024")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "2024"


def test_get_schedules_filter_multiple_params(client, db_session):
    """
    Multiple filters applied together return only the intersection.
    Catches cases where filters are OR'd instead of AND'd.
    """
    campus_a = _make_campus(db_session, "Boston")
    campus_b = _make_campus(db_session, "Oakland")
    _make_schedule(
        db_session, campus_a.campus_id, name="Match", semester=Semester.FALL, year=2024
    )
    _make_schedule(
        db_session,
        campus_b.campus_id,
        name="Wrong Campus",
        semester=Semester.FALL,
        year=2024,
    )
    _make_schedule(
        db_session,
        campus_a.campus_id,
        name="Wrong Year",
        semester=Semester.FALL,
        year=2025,
    )

    response = client.get(
        f"/schedules?campus_id={campus_a.campus_id}&semester_season=Fall&semester_year=2024"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Match"


def test_get_schedules_filter_no_match_returns_empty(client, db_session):
    """
    Filters that match nothing return 200 with an empty list, not 404.
    """
    campus = _make_campus(db_session)
    _make_schedule(db_session, campus.campus_id, year=2024)

    response = client.get("/schedules?semester_year=9999")
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# GET /schedules/{id} — get one
# ---------------------------------------------------------------------------


def test_get_schedule_by_id(client, db_session):
    """
    Returns the correct schedule when given a valid ID.
    """
    campus = _make_campus(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, name="Fall 2024")

    response = client.get(f"/schedules/{schedule.schedule_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Fall 2024"
    assert response.json()["schedule_id"] == schedule.schedule_id


def test_get_schedule_by_id_not_found(client, db_session):
    """
    Returns 404 when schedule ID does not exist.
    """
    response = client.get("/schedules/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_schedule_by_id_response_shape(client, db_session):
    """
    Single schedule response has all expected fields.
    """
    campus = _make_campus(db_session)
    schedule = _make_schedule(db_session, campus.campus_id)

    response = client.get(f"/schedules/{schedule.schedule_id}")
    data = response.json()
    expected_keys = {
        "schedule_id",
        "name",
        "semester",
        "year",
        "draft",
        "campus",
        "complete",
    }
    assert expected_keys.issubset(set(data.keys()))


def test_get_schedule_by_id_campus_is_int(client, db_session):
    """
    Campus field in response is the integer FK, not a string or enum.
    Catches serialization regression if campus type changes back to enum.
    """
    campus = _make_campus(db_session)
    schedule = _make_schedule(db_session, campus.campus_id)

    response = client.get(f"/schedules/{schedule.schedule_id}")
    assert isinstance(response.json()["campus"], int)
    assert response.json()["campus"] == campus.campus_id


# ---------------------------------------------------------------------------
# PUT /schedules/{id} — update
# ---------------------------------------------------------------------------


def test_update_schedule_name(client, db_session):
    """
    Updating name returns 200 with the new name reflected.
    """
    campus = _make_campus(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, name="Old Name")

    response = client.put(
        f"/schedules/{schedule.schedule_id}", json={"name": "New Name"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


def test_update_schedule_complete_flag(client, db_session):
    """
    Updating complete from False to True is persisted and returned.
    """
    campus = _make_campus(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, complete=False)

    response = client.put(f"/schedules/{schedule.schedule_id}", json={"complete": True})
    assert response.status_code == 200
    assert response.json()["complete"] is True


def test_update_schedule_partial_name_preserves_complete(client, db_session):
    """
    Partial update — only name — does not touch complete.
    Verifies model_dump(exclude_unset=True) is working correctly
    so untouched fields aren't overwritten with None.
    """
    campus = _make_campus(db_session)
    schedule = _make_schedule(
        db_session, campus.campus_id, name="Original", complete=True
    )

    response = client.put(
        f"/schedules/{schedule.schedule_id}", json={"name": "Updated"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"
    assert data["complete"] is True


def test_update_schedule_partial_complete_preserves_name(client, db_session):
    """
    Partial update — only complete — does not touch name.
    """
    campus = _make_campus(db_session)
    schedule = _make_schedule(
        db_session, campus.campus_id, name="Keep This Name", complete=False
    )

    response = client.put(f"/schedules/{schedule.schedule_id}", json={"complete": True})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Keep This Name"
    assert data["complete"] is True


def test_update_schedule_persisted_to_db(client, db_session):
    """
    After update the change is actually in the database, not just returned in the
    response. Guards against a service that returns the input without actually
    writing to DB.
    """
    campus = _make_campus(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, name="Before")

    client.put(f"/schedules/{schedule.schedule_id}", json={"name": "After"})

    db_session.expire_all()
    updated = db_session.get(Schedule, schedule.schedule_id)
    assert updated.name == "After"


def test_update_schedule_not_found(client, db_session):
    """
    Returns 404 when schedule ID does not exist.
    """
    response = client.put("/schedules/99999", json={"name": "Ghost"})
    assert response.status_code == 404


def test_update_schedule_empty_body(client, db_session):
    """
    Empty update body returns 200 with no fields changed.
    Verifies the endpoint doesn't error on a no-op update.
    """
    campus = _make_campus(db_session)
    schedule = _make_schedule(db_session, campus.campus_id, name="Unchanged")

    response = client.put(f"/schedules/{schedule.schedule_id}", json={})
    assert response.status_code == 200
    assert response.json()["name"] == "Unchanged"


def test_update_schedule_immutable_fields_ignored(client, db_session):
    """
    Fields not in ScheduleUpdate (semester, year, campus) are stripped by Pydantic.
    Sending them in the body should not change their values.
    """
    campus = _make_campus(db_session)
    schedule = _make_schedule(
        db_session, campus.campus_id, year=2024, semester=Semester.FALL
    )

    response = client.put(
        f"/schedules/{schedule.schedule_id}",
        json={"year": 9999, "semester": "Spring", "name": "Updated"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["year"] == 2024
    assert data["name"] == "Updated"


# ---------------------------------------------------------------------------
# DELETE /schedules/{id}
# ---------------------------------------------------------------------------


def test_delete_schedule(client, db_session):
    """
    Returns 204 No Content and the schedule is gone from the DB.
    """
    campus = _make_campus(db_session)
    schedule = _make_schedule(db_session, campus.campus_id)
    schedule_id = schedule.schedule_id

    response = client.delete(f"/schedules/{schedule_id}")
    assert response.status_code == 204

    db_session.expire_all()
    assert db_session.get(Schedule, schedule_id) is None


def test_delete_schedule_not_found(client, db_session):
    """
    Returns 404 when schedule ID does not exist.
    """
    response = client.delete("/schedules/99999")
    assert response.status_code == 404


def test_delete_schedule_no_response_body(client, db_session):
    """
    204 responses must have no body.
    FastAPI will error if a body is accidentally returned on a 204 endpoint.
    """
    campus = _make_campus(db_session)
    schedule = _make_schedule(db_session, campus.campus_id)

    response = client.delete(f"/schedules/{schedule.schedule_id}")
    assert response.status_code == 204
    assert response.content == b""


def test_delete_schedule_second_attempt_returns_404(client, db_session):
    """
    Deleting the same schedule twice returns 404 on the second attempt.
    Verifies the delete doesn't silently succeed on an already-deleted record.
    """
    campus = _make_campus(db_session)
    schedule = _make_schedule(db_session, campus.campus_id)
    schedule_id = schedule.schedule_id

    client.delete(f"/schedules/{schedule_id}")
    response = client.delete(f"/schedules/{schedule_id}")
    assert response.status_code == 404


def test_delete_schedule_no_longer_in_list(client, db_session):
    """
    After deletion the schedule does not appear in GET /schedules.
    """
    campus = _make_campus(db_session)
    schedule = _make_schedule(db_session, campus.campus_id)
    schedule_id = schedule.schedule_id

    client.delete(f"/schedules/{schedule_id}")

    response = client.get("/schedules")
    ids = [s["schedule_id"] for s in response.json()]
    assert schedule_id not in ids


# ---------------------------------------------------------------------------
# Boundary and default value tests
# ---------------------------------------------------------------------------


def test_schedule_year_boundary_min(client, db_session):
    """
    Year value of 1000 satisfies the DB check constraint (year >= 1000).
    """
    campus = _make_campus(db_session)
    schedule = Schedule(
        name="Min Year", semester=Semester.FALL, year=1000, campus=campus.campus_id
    )
    db_session.add(schedule)
    db_session.commit()

    response = client.get(f"/schedules/{schedule.schedule_id}")
    assert response.status_code == 200
    assert response.json()["year"] == 1000


def test_schedule_year_boundary_max(client, db_session):
    """
    Year value of 9999 satisfies the DB check constraint (year <= 9999).
    """
    campus = _make_campus(db_session)
    schedule = Schedule(
        name="Max Year", semester=Semester.FALL, year=9999, campus=campus.campus_id
    )
    db_session.add(schedule)
    db_session.commit()

    response = client.get(f"/schedules/{schedule.schedule_id}")
    assert response.status_code == 200
    assert response.json()["year"] == 9999


def test_schedule_draft_defaults_to_true(client, db_session):
    """
    draft field defaults to True — schedules always start as drafts.
    The algorithm populates sections; the user finalizes to complete.
    """
    campus = _make_campus(db_session)
    _make_schedule(db_session, campus.campus_id)

    response = client.get("/schedules")
    assert response.json()[0]["draft"] is True


def test_schedule_complete_defaults_to_false(client, db_session):
    """
    complete field defaults to False — schedules are not complete until finalized.
    """
    campus = _make_campus(db_session)
    _make_schedule(db_session, campus.campus_id)

    response = client.get("/schedules")
    assert response.json()[0]["complete"] is False


def test_multiple_schedules_same_campus(client, db_session):
    """
    Multiple schedules can share the same campus — no unique constraint on campus.
    A campus hosts many schedules across different semesters and years.
    """
    campus = _make_campus(db_session)
    _make_schedule(db_session, campus.campus_id, name="S1", year=2024)
    _make_schedule(db_session, campus.campus_id, name="S2", year=2025)

    response = client.get(f"/schedules?campus_id={campus.campus_id}")
    assert len(response.json()) == 2
