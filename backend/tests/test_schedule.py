from app.models import Schedule
from app.core.enums import Semester


def test_get_schedules_empty(client, db_session):
    response = client.get("/schedules")
    assert response.status_code == 200
    assert response.json() == []


def test_get_schedules_returns_all(client, db_session):
    db_session.add_all([
        Schedule(name="Fall 2024", semester=Semester.FALL, year=2024, campus=1),
        Schedule(name="Spring 2025", semester=Semester.SPRING, year=2025, campus=1),
    ])
    db_session.commit()

    response = client.get("/schedules")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_schedule_by_id(client, db_session):
    schedule = Schedule(name="Fall 2024", semester=Semester.FALL, year=2024, campus=1)
    db_session.add(schedule)
    db_session.commit()

    response = client.get(f"/schedules/{schedule.schedule_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Fall 2024"


def test_get_schedule_not_found(client, db_session):
    response = client.get("/schedules/99999")
    assert response.status_code == 404


def test_update_schedule(client, db_session):
    schedule = Schedule(name="Old Name", semester=Semester.FALL, year=2024, campus=1)
    db_session.add(schedule)
    db_session.commit()

    response = client.put(f"/schedules/{schedule.schedule_id}", json={"name": "New Name"})
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


def test_update_schedule_not_found(client, db_session):
    response = client.put("/schedules/99999", json={"name": "Ghost"})
    assert response.status_code == 404


def test_delete_schedule(client, db_session):
    schedule = Schedule(name="To Delete", semester=Semester.FALL, year=2024, campus=1)
    db_session.add(schedule)
    db_session.commit()
    schedule_id = schedule.schedule_id

    response = client.delete(f"/schedules/{schedule_id}")
    assert response.status_code == 204

    gone = db_session.get(Schedule, schedule_id)
    assert gone is None


def test_delete_schedule_not_found(client, db_session):
    response = client.delete("/schedules/99999")
    assert response.status_code == 404