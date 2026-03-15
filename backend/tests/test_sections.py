from app.models import Section


def test_get_sections_empty(client):
    response = client.get("/sections")
    assert response.status_code == 200
    assert response.json() == []


def test_get_sections_returns_all(client, db_session):
    db_session.add_all(
        [
            Section(Capacity=30),
            Section(Capacity=25),
        ]
    )
    db_session.commit()

    response = client.get("/sections")

    print("responseza:", response)

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_sections_response_shape(client, db_session):
    db_session.add(Section(Course=101, Capacity=20, Instructor=999))
    db_session.commit()

    response = client.get("/sections")
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


def test_get_sections_nullable_fields(client, db_session):
    # FK columns are nullable — a section with only Capacity set should
    # serialize cleanly.
    db_session.add(Section(Capacity=15))
    db_session.commit()

    response = client.get("/sections")
    section = response.json()[0]
    assert section["Capacity"] == 15
    assert section["Schedule"] is None
    assert section["TimeBlock"] is None
    assert section["Course"] is None
    assert section["Instructor"] is None
