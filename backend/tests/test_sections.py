from app.models import Schedule, Section


def test_get_schedule_sections_empty(client, db_session):
    schedule = Schedule(ScheduleName="Test", SemesterSeason="Fall", SemesterYear=2024, Campus=1)
    db_session.add(schedule)
    db_session.commit()
    
    response = client.get(f"/schedules/{schedule.ScheduleID}/sections")
    assert response.status_code == 200
    assert response.json() == []


def test_get_schedule_sections_returns_all(client, db_session):
    schedule = Schedule(ScheduleName="Test", SemesterSeason="Fall", SemesterYear=2024, Campus=1)
    db_session.add(schedule)
    db_session.commit()
    
    db_session.add_all(
        [
            Section(Schedule=schedule.ScheduleID, Capacity=30),
            Section(Schedule=schedule.ScheduleID, Capacity=25),
        ]
    )
    db_session.commit()

    response = client.get(f"/schedules/{schedule.ScheduleID}/sections")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_schedule_sections_response_shape(client, db_session):
    schedule = Schedule(ScheduleName="Test", SemesterSeason="Fall", SemesterYear=2024, Campus=1)
    db_session.add(schedule)
    db_session.commit()
    
    db_session.add(Section(Schedule=schedule.ScheduleID, Course=101, Capacity=20, Instructor=999))
    db_session.commit()

    response = client.get(f"/schedules/{schedule.ScheduleID}/sections")
    assert response.status_code == 200
    section = response.json()[0]
    expected_keys = {
        "SectionID",
        "Schedule",
        "TimeBlock",
        "Course",
        "Capacity",
        "Instructor",
    }
    assert set(section.keys()) == expected_keys


def test_get_schedule_sections_nullable_fields(client, db_session):
    schedule = Schedule(ScheduleName="Test", SemesterSeason="Fall", SemesterYear=2024, Campus=1)
    db_session.add(schedule)
    db_session.commit()
    
    # FK columns are nullable — a section with only Capacity set should
    # serialize cleanly.
    db_session.add(Section(Schedule=schedule.ScheduleID, Capacity=15))
    db_session.commit()

    response = client.get(f"/schedules/{schedule.ScheduleID}/sections")
    section = response.json()[0]
    assert section["Capacity"] == 15
    assert section["Schedule"] == schedule.ScheduleID
    assert section["TimeBlock"] is None
    assert section["Course"] is None
    assert section["Instructor"] is None
