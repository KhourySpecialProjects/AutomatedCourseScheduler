from app.core.enums import Semester
from app.models import Schedule, Section


def test_get_schedule_sections_empty(client, db_session):
    schedule = Schedule(name="Test", semester=Semester.FALL, year=2024)
    db_session.add(schedule)
    db_session.commit()

    response = client.get(f"/schedules/{schedule.schedule_id}/sections")
    assert response.status_code == 200
    assert response.json() == []


def test_get_schedule_sections_returns_all(client, db_session):
    schedule = Schedule(name="Test", semester=Semester.FALL, year=2024)
    db_session.add(schedule)
    db_session.commit()

    db_session.add_all(
        [
            Section(
                schedule_id=schedule.schedule_id,
                time_block_id=1,
                course_id=1,
                section_number=1,
                capacity=30,
            ),
            Section(
                schedule_id=schedule.schedule_id,
                time_block_id=2,
                course_id=2,
                section_number=2,
                capacity=25,
            ),
        ]
    )
    db_session.commit()

    response = client.get(f"/schedules/{schedule.schedule_id}/sections")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_schedule_sections_response_shape(client, db_session):
    schedule = Schedule(name="Test", semester=Semester.FALL, year=2024)
    db_session.add(schedule)
    db_session.commit()

    db_session.add(
        Section(
            schedule_id=schedule.schedule_id,
            time_block_id=1,
            course_id=101,
            section_number=1,
            capacity=20,
        )
    )
    db_session.commit()

    response = client.get(f"/schedules/{schedule.schedule_id}/sections")
    assert response.status_code == 200
    section = response.json()[0]
    expected_keys = {
        "section_id",
        "schedule_id",
        "time_block_id",
        "course_id",
        "capacity",
        "section_number",
        "assignment_score"
    }
    assert set(section.keys()) == expected_keys


def test_get_schedule_sections_field_values(client, db_session):
    schedule = Schedule(name="Test", semester=Semester.FALL, year=2024)
    db_session.add(schedule)
    db_session.commit()

    db_session.add(
        Section(
            schedule_id=schedule.schedule_id,
            time_block_id=5,
            course_id=101,
            section_number=3,
            capacity=15,
        )
    )
    db_session.commit()

    response = client.get(f"/schedules/{schedule.schedule_id}/sections")
    section = response.json()[0]
    assert section["capacity"] == 15
    assert section["schedule_id"] == schedule.schedule_id
    assert section["time_block_id"] == 5
    assert section["course_id"] == 101
    assert section["section_number"] == 3
