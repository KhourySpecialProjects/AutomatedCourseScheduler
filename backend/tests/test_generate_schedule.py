"""Tests for schedule generation endpoints and status lifecycle."""

from unittest.mock import patch

from app.core.enums import ScheduleStatus
from app.models import Schedule
from app.models.campus import Campus
from app.models.semester import Semester

_year = 2000


def _seed_schedule(db, status=ScheduleStatus.IDLE):
    global _year
    _year += 1
    campus = Campus(name="Boston")
    db.add(campus)
    db.flush()
    semester = Semester(season="Fall", year=_year)
    db.add(semester)
    db.flush()
    schedule = Schedule(
        name="Test",
        semester_id=semester.semester_id,
        campus=campus.campus_id,
        status=status,
    )
    db.add(schedule)
    db.commit()
    return schedule


def test_generate_returns_202(client, db_session):
    schedule = _seed_schedule(db_session)
    with patch("app.services.algorithm.run_algorithm_task"):
        response = client.post(
            f"/schedules/{schedule.schedule_id}/generate",
            json={},
        )
    assert response.status_code == 202
    data = response.json()
    assert data["schedule_id"] == schedule.schedule_id
    assert data["status"] == "running"


def test_generate_sets_status_to_running(client, db_session):
    schedule = _seed_schedule(db_session)
    with patch("app.services.algorithm.run_algorithm_task"):
        client.post(f"/schedules/{schedule.schedule_id}/generate", json={})
    db_session.expire_all()
    reloaded = db_session.get(Schedule, schedule.schedule_id)
    assert reloaded.status == ScheduleStatus.RUNNING
    assert reloaded.started_at is not None
    assert reloaded.completed_at is None
    assert reloaded.error_message is None


def test_generate_409_when_already_running(client, db_session):
    schedule = _seed_schedule(db_session, status=ScheduleStatus.RUNNING)
    response = client.post(
        f"/schedules/{schedule.schedule_id}/generate",
        json={},
    )
    assert response.status_code == 409
    assert "already running" in response.json()["detail"].lower()


def test_generate_404_when_schedule_not_found(client, db_session):
    response = client.post("/schedules/99999/generate", json={})
    assert response.status_code == 404


def test_generate_clears_previous_error(client, db_session):
    schedule = _seed_schedule(db_session, status=ScheduleStatus.FAILED)
    schedule.error_message = "Previous failure"
    db_session.commit()
    with patch("app.services.algorithm.run_algorithm_task"):
        client.post(f"/schedules/{schedule.schedule_id}/generate", json={})
    db_session.expire_all()
    reloaded = db_session.get(Schedule, schedule.schedule_id)
    assert reloaded.error_message is None
    assert reloaded.status == ScheduleStatus.RUNNING


def test_generate_allowed_after_failure(client, db_session):
    schedule = _seed_schedule(db_session, status=ScheduleStatus.FAILED)
    with patch("app.services.algorithm.run_algorithm_task"):
        response = client.post(
            f"/schedules/{schedule.schedule_id}/generate",
            json={},
        )
    assert response.status_code == 202


def test_generate_allowed_after_success(client, db_session):
    schedule = _seed_schedule(db_session, status=ScheduleStatus.GENERATED)
    with patch("app.services.algorithm.run_algorithm_task"):
        response = client.post(
            f"/schedules/{schedule.schedule_id}/generate",
            json={},
        )
    assert response.status_code == 202


def test_regenerate_returns_202(client, db_session):
    schedule = _seed_schedule(db_session)
    with patch("app.services.algorithm.run_regenerate_task"):
        response = client.post(
            f"/schedules/{schedule.schedule_id}/regenerate",
            json={},
        )
    assert response.status_code == 202


def test_regenerate_sets_status_to_running(client, db_session):
    schedule = _seed_schedule(db_session)
    with patch("app.services.algorithm.run_regenerate_task"):
        client.post(f"/schedules/{schedule.schedule_id}/regenerate", json={})
    db_session.expire_all()
    reloaded = db_session.get(Schedule, schedule.schedule_id)
    assert reloaded.status == ScheduleStatus.RUNNING


def test_regenerate_409_when_already_running(client, db_session):
    schedule = _seed_schedule(db_session, status=ScheduleStatus.RUNNING)
    response = client.post(
        f"/schedules/{schedule.schedule_id}/regenerate",
        json={},
    )
    assert response.status_code == 409


def test_regenerate_404_when_schedule_not_found(client, db_session):
    response = client.post("/schedules/99999/regenerate", json={})
    assert response.status_code == 404


def test_schedule_response_includes_status(client, db_session):
    schedule = _seed_schedule(db_session)
    response = client.get(f"/schedules/{schedule.schedule_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "idle"


def test_schedule_response_includes_error_message(client, db_session):
    schedule = _seed_schedule(db_session, status=ScheduleStatus.FAILED)
    schedule.error_message = "Something broke"
    db_session.commit()
    response = client.get(f"/schedules/{schedule.schedule_id}")
    data = response.json()
    assert data["status"] == "failed"
    assert data["error_message"] == "Something broke"
