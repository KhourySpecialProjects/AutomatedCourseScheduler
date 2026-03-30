from datetime import time

from app.core.enums import PreferenceLevel, Semester
from app.models import (
    Campus,
    Course,
    CoursePreference,
    Faculty,
    FacultyAssignment,
    MeetingPreference,
    Schedule,
    Section,
    TimeBlock,
)


def test_get_schedule_sections_empty(client, db_session):
    schedule = Schedule(
        name="Test", semester=Semester.FALL, year=2024, campus=Campus.BOSTON
    )
    db_session.add(schedule)
    db_session.commit()

    response = client.get(f"/schedules/{schedule.schedule_id}/sections")
    assert response.status_code == 200
    assert response.json() == []


def test_get_schedule_sections_returns_all(client, db_session):
    schedule, course, time_block = _seed_schedule_course_timeblock(db_session)

    db_session.add_all(
        [
            Section(
                schedule_id=schedule.schedule_id,
                time_block_id=time_block.time_block_id,
                course_id=course.course_id,
                section_number=1,
                capacity=30,
            ),
            Section(
                schedule_id=schedule.schedule_id,
                time_block_id=time_block.time_block_id,
                course_id=course.course_id,
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
    schedule, course, time_block = _seed_schedule_course_timeblock(db_session)

    db_session.add(
        Section(
            schedule_id=schedule.schedule_id,
            time_block_id=time_block.time_block_id,
            course_id=course.course_id,
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
        "room",
        "assignment_score",
    }
    assert set(section.keys()) == expected_keys


def test_get_schedule_sections_field_values(client, db_session):
    schedule, course, time_block = _seed_schedule_course_timeblock(db_session)

    db_session.add(
        Section(
            schedule_id=schedule.schedule_id,
            time_block_id=time_block.time_block_id,
            course_id=course.course_id,
            section_number=3,
            capacity=15,
        )
    )
    db_session.commit()

    response = client.get(f"/schedules/{schedule.schedule_id}/sections")
    section = response.json()[0]
    assert section["capacity"] == 15
    assert section["schedule_id"] == schedule.schedule_id
    assert section["time_block_id"] == time_block.time_block_id
    assert section["course_id"] == course.course_id
    assert section["section_number"] == 3


def test_get_schedule_sections_unknown_schedule_returns_404(client, db_session):
    assert client.get("/schedules/99999/sections").status_code == 404


def test_get_rich_sections_empty(client, db_session):
    schedule = Schedule(name="Test", semester=Semester.FALL, year=2024)
    db_session.add(schedule)
    db_session.commit()

    response = client.get(f"/schedules/{schedule.schedule_id}/sections/rich")
    assert response.status_code == 200
    assert response.json() == []


def test_get_rich_sections_unknown_schedule_returns_404(client, db_session):
    assert client.get("/schedules/99999/sections/rich").status_code == 404


def test_get_rich_sections_nested_shape(client, db_session):
    schedule = Schedule(name="Sched", semester=Semester.FALL, year=2025)
    course = Course(name="Intro CS", description="Fun", credits=4)
    campus = Campus(name="Boston")
    db_session.add_all([schedule, course, campus])
    db_session.flush()
    tb = TimeBlock(
        meeting_days="MW",
        start_time=time(10, 30),
        end_time=time(11, 45),
        campus=campus.campus_id,
    )
    faculty = Faculty(
        nuid=1001,
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.edu",
        title=None,
        campus="Boston",
    )
    db_session.add_all([tb, faculty])
    db_session.flush()

    section = Section(
        schedule_id=schedule.schedule_id,
        time_block_id=tb.time_block_id,
        course_id=course.course_id,
        section_number=1,
        capacity=40,
    )
    db_session.add(section)
    db_session.flush()

    db_session.add(
        FacultyAssignment(faculty_nuid=faculty.nuid, section_id=section.section_id)
    )
    db_session.add(
        CoursePreference(
            faculty_nuid=faculty.nuid,
            course_id=course.course_id,
            preference=PreferenceLevel.EAGER,
        )
    )
    db_session.add(
        MeetingPreference(
            faculty_nuid=faculty.nuid,
            meeting_time=tb.time_block_id,
            preference=PreferenceLevel.READY,
        )
    )
    db_session.commit()

    response = client.get(f"/schedules/{schedule.schedule_id}/sections/rich")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    row = payload[0]
    assert row["section_number"] == 1
    assert row["capacity"] == 40
    assert row["course"]["name"] == "Intro CS"
    assert row["time_block"]["days"] == "MW"
    assert row["time_block"]["start_time"] != ""
    assert len(row["instructors"]) == 1
    inst = row["instructors"][0]
    assert inst["nuid"] == 1001
    assert inst["title"] == ""
    assert len(inst["course_preferences"]) == 1
    assert inst["course_preferences"][0]["course_name"] == "Intro CS"
    assert len(inst["meeting_preferences"]) == 1
    assert inst["meeting_preferences"][0]["meeting_time"] == str(tb.time_block_id)


def _seed_schedule_course_timeblock(db_session):
    schedule = Schedule(name="F24", semester=Semester.FALL, year=2024)
    course = Course(name="CS 2500", description="Fundamentals", credits=4)
    campus = Campus(name="Boston")
    db_session.add_all([schedule, course, campus])
    db_session.flush()
    time_block = TimeBlock(
        meeting_days="MW",
        start_time=time(10, 0),
        end_time=time(11, 0),
        campus=campus.campus_id,
    )
    db_session.add(time_block)
    db_session.commit()
    return schedule, course, time_block


def test_create_section_success(client, db_session):
    schedule, course, time_block = _seed_schedule_course_timeblock(db_session)

    response = client.post(
        "/sections",
        json={
            "schedule_id": schedule.schedule_id,
            "time_block_id": time_block.time_block_id,
            "course_id": course.course_id,
            "capacity": 30,
            "section_number": 1,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["schedule_id"] == schedule.schedule_id
    assert data["course_id"] == course.course_id
    assert data["time_block_id"] == time_block.time_block_id
    assert data["capacity"] == 30
    assert data["section_number"] == 1


def test_create_section_invalid_schedule_returns_400(client, db_session):
    _, course, time_block = _seed_schedule_course_timeblock(db_session)

    response = client.post(
        "/sections",
        json={
            "schedule_id": 99999,
            "time_block_id": time_block.time_block_id,
            "course_id": course.course_id,
            "capacity": 30,
            "section_number": 1,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "ScheduleID is invalid"


def test_create_section_invalid_course_returns_400(client, db_session):
    schedule, _, time_block = _seed_schedule_course_timeblock(db_session)

    response = client.post(
        "/sections",
        json={
            "schedule_id": schedule.schedule_id,
            "time_block_id": time_block.time_block_id,
            "course_id": 99999,
            "capacity": 30,
            "section_number": 1,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "CourseID is invalid"


def test_patch_section_success(client, db_session):
    schedule, course, time_block = _seed_schedule_course_timeblock(db_session)
    new_course = Course(name="CS 3200", description="Databases", credits=4)
    campus = Campus(name="Boston")
    db_session.add_all([new_course, campus])
    db_session.flush()
    new_time_block = TimeBlock(
        meeting_days="TR",
        start_time=time(12, 0),
        end_time=time(13, 0),
        campus=campus.campus_id,
    )
    db_session.add(new_time_block)
    db_session.flush()
    crosslisted_target = Section(
        schedule_id=schedule.schedule_id,
        time_block_id=time_block.time_block_id,
        course_id=course.course_id,
        capacity=20,
        section_number=2,
    )
    db_session.add(crosslisted_target)
    db_session.flush()

    section = Section(
        schedule_id=schedule.schedule_id,
        time_block_id=time_block.time_block_id,
        course_id=course.course_id,
        capacity=25,
        section_number=1,
    )
    db_session.add(section)
    db_session.commit()

    response = client.patch(
        f"/sections/{section.section_id}",
        json={
            "time_block_id": new_time_block.time_block_id,
            "course_id": new_course.course_id,
            "capacity": 40,
            "room": "WVH108",
            "crosslisted_section_id": crosslisted_target.section_id,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["schedule_id"] == schedule.schedule_id
    assert data["time_block_id"] == new_time_block.time_block_id
    assert data["course_id"] == new_course.course_id
    assert data["capacity"] == 40
    assert data["section_number"] == 1


def test_patch_section_not_found_returns_404(client, db_session):
    response = client.patch("/sections/99999", json={"capacity": 10})
    assert response.status_code == 404
    assert response.json()["detail"] == "Section not found"


def test_patch_section_invalid_time_block_returns_400(client, db_session):
    schedule, course, time_block = _seed_schedule_course_timeblock(db_session)
    section = Section(
        schedule_id=schedule.schedule_id,
        time_block_id=time_block.time_block_id,
        course_id=course.course_id,
        capacity=25,
        section_number=1,
    )
    db_session.add(section)
    db_session.commit()

    response = client.patch(
        f"/sections/{section.section_id}",
        json={"time_block_id": 99999},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "TimeBlockID is invalid"


def test_patch_section_invalid_course_returns_400(client, db_session):
    schedule, course, time_block = _seed_schedule_course_timeblock(db_session)
    section = Section(
        schedule_id=schedule.schedule_id,
        time_block_id=time_block.time_block_id,
        course_id=course.course_id,
        capacity=25,
        section_number=1,
    )
    db_session.add(section)
    db_session.commit()

    response = client.patch(
        f"/sections/{section.section_id}",
        json={"course_id": 99999},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "CourseID is invalid"


def test_patch_section_invalid_crosslisted_returns_400(client, db_session):
    schedule, course, time_block = _seed_schedule_course_timeblock(db_session)
    section = Section(
        schedule_id=schedule.schedule_id,
        time_block_id=time_block.time_block_id,
        course_id=course.course_id,
        capacity=25,
        section_number=1,
    )
    db_session.add(section)
    db_session.commit()

    response = client.patch(
        f"/sections/{section.section_id}",
        json={"crosslisted_section_id": 99999},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "CrosslistedSectionID is invalid"


def test_patch_section_clear_nullable_fields(client, db_session):
    schedule, course, time_block = _seed_schedule_course_timeblock(db_session)
    target = Section(
        schedule_id=schedule.schedule_id,
        time_block_id=time_block.time_block_id,
        course_id=course.course_id,
        capacity=25,
        section_number=1,
        room="WVH110",
    )
    other = Section(
        schedule_id=schedule.schedule_id,
        time_block_id=time_block.time_block_id,
        course_id=course.course_id,
        capacity=20,
        section_number=2,
    )
    db_session.add_all([target, other])
    db_session.flush()
    target.crosslisted_section_id = other.section_id
    db_session.commit()

    response = client.patch(
        f"/sections/{target.section_id}",
        json={"room": None, "crosslisted_section_id": None},
    )
    assert response.status_code == 200

    reloaded = (
        db_session.query(Section)
        .filter(Section.section_id == target.section_id)
        .first()
    )
    assert reloaded is not None
    assert reloaded.room is None
    assert reloaded.crosslisted_section_id is None


def test_patch_section_replace_faculty_assignments(client, db_session):
    schedule, course, time_block = _seed_schedule_course_timeblock(db_session)
    section = Section(
        schedule_id=schedule.schedule_id,
        time_block_id=time_block.time_block_id,
        course_id=course.course_id,
        capacity=25,
        section_number=1,
    )
    f1 = Faculty(
        nuid=1001,
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        campus="Boston",
    )
    f2 = Faculty(
        nuid=1002,
        first_name="John",
        last_name="Smith",
        email="john@example.com",
        campus="Boston",
    )
    db_session.add_all([section, f1, f2])
    db_session.flush()
    db_session.add(
        FacultyAssignment(faculty_nuid=f1.nuid, section_id=section.section_id)
    )
    db_session.commit()

    response = client.patch(
        f"/sections/{section.section_id}",
        json={"faculty_nuids": [f2.nuid]},
    )
    assert response.status_code == 200

    assignments = (
        db_session.query(FacultyAssignment)
        .filter(FacultyAssignment.section_id == section.section_id)
        .all()
    )
    assert len(assignments) == 1
    assert assignments[0].faculty_nuid == f2.nuid


def test_patch_section_invalid_faculty_assignments_returns_400(client, db_session):
    schedule, course, time_block = _seed_schedule_course_timeblock(db_session)
    section = Section(
        schedule_id=schedule.schedule_id,
        time_block_id=time_block.time_block_id,
        course_id=course.course_id,
        capacity=25,
        section_number=1,
    )
    db_session.add(section)
    db_session.commit()

    response = client.patch(
        f"/sections/{section.section_id}",
        json={"faculty_nuids": [99999]},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "FacultyNUIDs is invalid"


def test_delete_section_success(client, db_session):
    schedule, course, time_block = _seed_schedule_course_timeblock(db_session)
    section = Section(
        schedule_id=schedule.schedule_id,
        time_block_id=time_block.time_block_id,
        course_id=course.course_id,
        capacity=25,
        section_number=1,
    )
    db_session.add(section)
    db_session.commit()

    response = client.delete(f"/sections/{section.section_id}")
    assert response.status_code == 204

    check = (
        db_session.query(Section)
        .filter(Section.section_id == section.section_id)
        .first()
    )
    assert check is None


def test_delete_section_not_found_returns_404(client, db_session):
    response = client.delete("/sections/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Section not found"
