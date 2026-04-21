"""Tests for schedule warning CRUD endpoints."""

from app.core.enums import WarningType
from app.models import Schedule
from app.models.campus import Campus
from app.models.schedule_warning import ScheduleWarning
from app.models.semester import Semester


def _seed_schedule(db, season="Fall", year=None):
    if year is None:
        year = db.query(Semester).count() + 4000
    campus = Campus(name="Boston")
    db.add(campus)
    db.flush()
    semester = Semester(season=season, year=year)
    db.add(semester)
    db.flush()
    schedule = Schedule(
        name="Test",
        semester_id=semester.semester_id,
        campus=campus.campus_id,
    )
    db.add(schedule)
    db.commit()
    return schedule


def _seed_warning(
    db,
    schedule_id,
    type="unmatched",
    severity="2",
    message="Test warning",
    dismissed=False,
    faculty_nuid=None,
    course_id=None,
    time_block_id=None,
):
    w = ScheduleWarning(
        schedule_id=schedule_id,
        type=type,
        severity=severity,
        message=message,
        dismissed=dismissed,
        faculty_nuid=faculty_nuid,
        course_id=course_id,
        time_block_id=time_block_id,
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    return w


# GET warnings


def test_get_warnings_empty(client, db_session):
    schedule = _seed_schedule(db_session)
    response = client.get(f"/schedules/{schedule.schedule_id}/warnings")
    assert response.status_code == 200
    assert response.json() == []


def test_get_warnings_returns_persisted(client, db_session):
    schedule = _seed_schedule(db_session)
    _seed_warning(db_session, schedule.schedule_id, message="Section unmatched")
    _seed_warning(db_session, schedule.schedule_id, message="Time block issue")

    response = client.get(f"/schedules/{schedule.schedule_id}/warnings")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    messages = {w["Message"] for w in data}
    assert "Section unmatched" in messages
    assert "Time block issue" in messages


def test_get_warnings_includes_warning_id(client, db_session):
    schedule = _seed_schedule(db_session)
    _seed_warning(db_session, schedule.schedule_id)
    response = client.get(f"/schedules/{schedule.schedule_id}/warnings")
    data = response.json()
    assert "warning_id" in data[0]
    assert isinstance(data[0]["warning_id"], int)


def test_get_warnings_includes_dismissed_field(client, db_session):
    schedule = _seed_schedule(db_session)
    _seed_warning(db_session, schedule.schedule_id)
    response = client.get(f"/schedules/{schedule.schedule_id}/warnings")
    data = response.json()
    assert "dismissed" in data[0]
    assert data[0]["dismissed"] is False


def test_get_warnings_filter_by_type(client, db_session):
    schedule = _seed_schedule(db_session)
    _seed_warning(db_session, schedule.schedule_id, type="unmatched")
    _seed_warning(db_session, schedule.schedule_id, type=WarningType.FACULTY_OVERLOAD.value)

    response = client.get(f"/schedules/{schedule.schedule_id}/warnings?type=unmatched")
    data = response.json()
    assert len(data) == 1
    assert data[0]["Type"] is None  # "unmatched" is not a WarningType enum value


def test_get_warnings_filter_by_severity(client, db_session):
    schedule = _seed_schedule(db_session)
    _seed_warning(db_session, schedule.schedule_id, severity="2")
    _seed_warning(db_session, schedule.schedule_id, severity="3")

    response = client.get(f"/schedules/{schedule.schedule_id}/warnings?severity=3")
    data = response.json()
    assert len(data) == 1
    assert data[0]["SeverityRank"] == 3


def test_get_warnings_excludes_dismissed_by_default(client, db_session):
    schedule = _seed_schedule(db_session)
    _seed_warning(db_session, schedule.schedule_id, dismissed=False)
    _seed_warning(db_session, schedule.schedule_id, dismissed=True)

    response = client.get(f"/schedules/{schedule.schedule_id}/warnings")
    data = response.json()
    assert len(data) == 1
    assert data[0]["dismissed"] is False


def test_get_warnings_include_dismissed(client, db_session):
    schedule = _seed_schedule(db_session)
    _seed_warning(db_session, schedule.schedule_id, dismissed=False)
    _seed_warning(db_session, schedule.schedule_id, dismissed=True)

    response = client.get(f"/schedules/{schedule.schedule_id}/warnings?include_dismissed=true")
    data = response.json()
    assert len(data) == 2


def test_get_warnings_404_for_missing_schedule(client, db_session):
    response = client.get("/schedules/99999/warnings")
    assert response.status_code == 404


def test_get_warnings_isolated_to_schedule(client, db_session):
    s1 = _seed_schedule(db_session)
    s2 = _seed_schedule(db_session)
    _seed_warning(db_session, s1.schedule_id, message="Warning on S1")
    _seed_warning(db_session, s2.schedule_id, message="Warning on S2")

    response = client.get(f"/schedules/{s1.schedule_id}/warnings")
    data = response.json()
    assert len(data) == 1
    assert data[0]["Message"] == "Warning on S1"


# POST warnings


def test_create_warning_success(client, db_session):
    schedule = _seed_schedule(db_session)
    response = client.post(
        f"/schedules/{schedule.schedule_id}/warnings",
        json={
            "SeverityRank": 2,
            "Message": "Manual warning from scheduler",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["Message"] == "Manual warning from scheduler"
    assert data["SeverityRank"] == 2
    assert "warning_id" in data
    assert data["dismissed"] is False


def test_create_warning_with_all_fields(client, db_session):
    schedule = _seed_schedule(db_session)
    response = client.post(
        f"/schedules/{schedule.schedule_id}/warnings",
        json={
            "Type": WarningType.FACULTY_OVERLOAD.value,
            "SeverityRank": 3,
            "Message": "Faculty 100 has too many sections",
            "FacultyID": 100,
            "CourseID": 42,
            "BlockID": 7,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["FacultyID"] == 100
    assert data["CourseID"] == 42
    assert data["BlockID"] == 7


def test_create_warning_persisted_to_db(client, db_session):
    schedule = _seed_schedule(db_session)
    client.post(
        f"/schedules/{schedule.schedule_id}/warnings",
        json={"SeverityRank": 2, "Message": "Persisted"},
    )
    db_session.expire_all()
    warnings = db_session.query(ScheduleWarning).filter(ScheduleWarning.schedule_id == schedule.schedule_id).all()
    assert len(warnings) == 1
    assert warnings[0].message == "Persisted"


def test_create_warning_404_for_missing_schedule(client, db_session):
    response = client.post(
        "/schedules/99999/warnings",
        json={"SeverityRank": 2, "Message": "Orphan"},
    )
    assert response.status_code == 404


# PATCH dismiss


def test_dismiss_warning(client, db_session):
    schedule = _seed_schedule(db_session)
    w = _seed_warning(db_session, schedule.schedule_id)

    response = client.patch(f"/schedules/{schedule.schedule_id}/warnings/{w.warning_id}/dismiss")
    assert response.status_code == 200
    assert response.json()["dismissed"] is True

    db_session.expire_all()
    reloaded = db_session.get(ScheduleWarning, w.warning_id)
    assert reloaded.dismissed is True


def test_dismiss_already_dismissed_is_idempotent(client, db_session):
    schedule = _seed_schedule(db_session)
    w = _seed_warning(db_session, schedule.schedule_id, dismissed=True)

    response = client.patch(f"/schedules/{schedule.schedule_id}/warnings/{w.warning_id}/dismiss")
    assert response.status_code == 200
    assert response.json()["dismissed"] is True


def test_dismiss_404_wrong_schedule(client, db_session):
    s1 = _seed_schedule(db_session)
    s2 = _seed_schedule(db_session)
    w = _seed_warning(db_session, s1.schedule_id)

    response = client.patch(f"/schedules/{s2.schedule_id}/warnings/{w.warning_id}/dismiss")
    assert response.status_code == 404


def test_dismiss_404_missing_warning(client, db_session):
    schedule = _seed_schedule(db_session)
    response = client.patch(f"/schedules/{schedule.schedule_id}/warnings/99999/dismiss")
    assert response.status_code == 404


# PATCH restore


def test_restore_warning(client, db_session):
    schedule = _seed_schedule(db_session)
    w = _seed_warning(db_session, schedule.schedule_id, dismissed=True)

    response = client.patch(f"/schedules/{schedule.schedule_id}/warnings/{w.warning_id}/restore")
    assert response.status_code == 200
    assert response.json()["dismissed"] is False

    db_session.expire_all()
    reloaded = db_session.get(ScheduleWarning, w.warning_id)
    assert reloaded.dismissed is False


def test_restore_non_dismissed_is_idempotent(client, db_session):
    schedule = _seed_schedule(db_session)
    w = _seed_warning(db_session, schedule.schedule_id, dismissed=False)

    response = client.patch(f"/schedules/{schedule.schedule_id}/warnings/{w.warning_id}/restore")
    assert response.status_code == 200
    assert response.json()["dismissed"] is False


def test_restore_404_wrong_schedule(client, db_session):
    s1 = _seed_schedule(db_session)
    s2 = _seed_schedule(db_session)
    w = _seed_warning(db_session, s1.schedule_id, dismissed=True)

    response = client.patch(f"/schedules/{s2.schedule_id}/warnings/{w.warning_id}/restore")
    assert response.status_code == 404


# DELETE warning


def test_delete_warning(client, db_session):
    schedule = _seed_schedule(db_session)
    w = _seed_warning(db_session, schedule.schedule_id)

    response = client.delete(f"/schedules/{schedule.schedule_id}/warnings/{w.warning_id}")
    assert response.status_code == 204

    db_session.expire_all()
    assert db_session.get(ScheduleWarning, w.warning_id) is None


def test_delete_warning_404_missing(client, db_session):
    schedule = _seed_schedule(db_session)
    response = client.delete(f"/schedules/{schedule.schedule_id}/warnings/99999")
    assert response.status_code == 404


def test_delete_warning_404_wrong_schedule(client, db_session):
    s1 = _seed_schedule(db_session)
    s2 = _seed_schedule(db_session)
    w = _seed_warning(db_session, s1.schedule_id)

    response = client.delete(f"/schedules/{s2.schedule_id}/warnings/{w.warning_id}")
    assert response.status_code == 404


def test_delete_does_not_affect_other_warnings(client, db_session):
    schedule = _seed_schedule(db_session)
    _seed_warning(db_session, schedule.schedule_id, message="Keep")
    w2 = _seed_warning(db_session, schedule.schedule_id, message="Delete")

    client.delete(f"/schedules/{schedule.schedule_id}/warnings/{w2.warning_id}")

    response = client.get(f"/schedules/{schedule.schedule_id}/warnings")
    data = response.json()
    assert len(data) == 1
    assert data[0]["Message"] == "Keep"
