from datetime import time

from app.core.enums import PreferenceLevel
from app.models import (
    Comment,
    Course,
    CoursePreference,
    Faculty,
    FacultyAssignment,
    MeetingPreference,
    Schedule,
    Section,
    TimeBlock,
    User,
)
from app.models.campus import Campus as CampusModel
from app.models.semester import Semester as SemesterModel

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_campus(db, name="Boston"):
    campus = CampusModel(name=name)
    db.add(campus)
    db.flush()
    return campus


def _make_semester(db, season="Fall", year=2024):
    semester = SemesterModel(season=season, year=year)
    db.add(semester)
    db.flush()
    return semester


def _seed_schedule_course_timeblock(db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = Schedule(name="F24", semester_id=semester.semester_id, campus=campus.campus_id)
    course = Course(subject="CS", code=2500, name="CS 2500", description="Fundamentals", credits=4)
    db_session.add_all([schedule, course])
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


# ---------------------------------------------------------------------------
# GET /schedules/{id}/sections
# ---------------------------------------------------------------------------


def test_get_schedule_sections_empty(client, db_session):
    schedule, _, __ = _seed_schedule_course_timeblock(db_session)
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


# ---------------------------------------------------------------------------
# GET /schedules/{id}/sections/rich
# ---------------------------------------------------------------------------


def test_get_rich_sections_empty(client, db_session):
    schedule, _, __ = _seed_schedule_course_timeblock(db_session)
    response = client.get(f"/schedules/{schedule.schedule_id}/sections/rich")
    assert response.status_code == 200
    assert response.json() == []


def test_get_rich_sections_unknown_schedule_returns_404(client, db_session):
    assert client.get("/schedules/99999/sections/rich").status_code == 404


def test_get_rich_sections_nested_shape(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)

    schedule = Schedule(name="Sched", semester_id=semester.semester_id, campus=campus.campus_id)
    course = Course(subject="CS", code=2500, name="Intro CS", description="Fun", credits=4)
    db_session.add_all([schedule, course])
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
        campus=campus.campus_id,
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

    db_session.add(FacultyAssignment(faculty_nuid=faculty.nuid, section_id=section.section_id))
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
    assert len(inst["course_preferences"]) == 1
    assert inst["course_preferences"][0]["course_name"] == "Intro CS"
    assert len(inst["meeting_preferences"]) == 1
    assert inst["meeting_preferences"][0]["time_block_id"] == tb.time_block_id
    assert row["comment_count"] == 0
    assert row["crosslisted_section_id"] is None


def test_get_rich_sections_includes_comment_count(client, db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)

    schedule = Schedule(name="Sched", semester_id=semester.semester_id, campus=campus.campus_id)
    course = Course(name="Intro CS", description="Fun", credits=4)
    db_session.add_all([schedule, course])
    db_session.flush()

    tb = TimeBlock(
        meeting_days="MW",
        start_time=time(10, 30),
        end_time=time(11, 45),
        campus=campus.campus_id,
    )
    db_session.add(tb)
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

    user = User(
        nuid=5001,
        first_name="Test",
        last_name="User",
        email="commentcount@test.edu",
        role="ADMIN",
    )
    db_session.add(user)
    db_session.flush()

    db_session.add_all(
        [
            Comment(user_id=user.user_id, section_id=section.section_id, content="One"),
            Comment(user_id=user.user_id, section_id=section.section_id, content="Two"),
        ]
    )
    db_session.commit()

    response = client.get(f"/schedules/{schedule.schedule_id}/sections/rich")
    assert response.status_code == 200
    row = response.json()[0]
    assert row["comment_count"] == 2


# ---------------------------------------------------------------------------
# POST /sections
# ---------------------------------------------------------------------------


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


def test_create_section_omitted_capacity_defaults_to_30(client, db_session):
    schedule, course, time_block = _seed_schedule_course_timeblock(db_session)
    response = client.post(
        "/sections",
        json={
            "schedule_id": schedule.schedule_id,
            "time_block_id": time_block.time_block_id,
            "course_id": course.course_id,
            "section_number": 1,
        },
    )
    assert response.status_code == 201
    assert response.json()["capacity"] == 30


def test_create_section_duplicate_course_section_number_returns_400(client, db_session):
    schedule, course, time_block = _seed_schedule_course_timeblock(db_session)
    db_session.add(
        Section(
            schedule_id=schedule.schedule_id,
            time_block_id=time_block.time_block_id,
            course_id=course.course_id,
            capacity=25,
            section_number=1,
        )
    )
    db_session.commit()
    response = client.post(
        "/sections",
        json={
            "schedule_id": schedule.schedule_id,
            "time_block_id": time_block.time_block_id,
            "course_id": course.course_id,
            "section_number": 1,
        },
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


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


# ---------------------------------------------------------------------------
# PATCH /sections/{id}
# ---------------------------------------------------------------------------


def test_patch_section_success(client, db_session):
    schedule, course, time_block = _seed_schedule_course_timeblock(db_session)
    campus = _make_campus(db_session, "Oakland")
    new_course = Course(subject="CS", code=3200, name="CS 3200", description="Databases", credits=4)
    db_session.add(new_course)
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

    db_session.refresh(crosslisted_target)
    assert crosslisted_target.time_block_id == new_time_block.time_block_id


def test_patch_section_crosslisted_syncs_partner_instructors(client, db_session):
    schedule, course, time_block = _seed_schedule_course_timeblock(db_session)
    campus = _make_campus(db_session, "Oakland")
    partner = Section(
        schedule_id=schedule.schedule_id,
        time_block_id=time_block.time_block_id,
        course_id=course.course_id,
        capacity=20,
        section_number=2,
    )
    section = Section(
        schedule_id=schedule.schedule_id,
        time_block_id=time_block.time_block_id,
        course_id=course.course_id,
        capacity=25,
        section_number=1,
    )
    f1 = Faculty(
        nuid=9001,
        first_name="A",
        last_name="One",
        email="a1@example.com",
        campus=campus.campus_id,
    )
    f2 = Faculty(
        nuid=9002,
        first_name="B",
        last_name="Two",
        email="b2@example.com",
        campus=campus.campus_id,
    )
    db_session.add_all([partner, section, f1, f2])
    db_session.flush()
    db_session.add(FacultyAssignment(faculty_nuid=f1.nuid, section_id=section.section_id))
    db_session.add(FacultyAssignment(faculty_nuid=f2.nuid, section_id=partner.section_id))
    db_session.commit()

    response = client.patch(
        f"/sections/{section.section_id}",
        json={"crosslisted_section_id": partner.section_id},
    )
    assert response.status_code == 200

    nuids_partner = (
        db_session.query(FacultyAssignment.faculty_nuid)
        .filter(FacultyAssignment.section_id == partner.section_id)
        .order_by(FacultyAssignment.faculty_assignment_id)
        .all()
    )
    assert [n[0] for n in nuids_partner] == [f1.nuid]


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

    response = client.patch(f"/sections/{section.section_id}", json={"time_block_id": 99999})
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
    response = client.patch(f"/sections/{section.section_id}", json={"course_id": 99999})
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
        f"/sections/{section.section_id}", json={"crosslisted_section_id": 99999}
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

    reloaded = db_session.query(Section).filter(Section.section_id == target.section_id).first()
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
    campus = _make_campus(db_session, "Oakland")
    f1 = Faculty(
        nuid=1001,
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        campus=campus.campus_id,
    )
    f2 = Faculty(
        nuid=1002,
        first_name="John",
        last_name="Smith",
        email="john@example.com",
        campus=campus.campus_id,
    )
    db_session.add_all([section, f1, f2])
    db_session.flush()
    db_session.add(FacultyAssignment(faculty_nuid=f1.nuid, section_id=section.section_id))
    db_session.commit()
    response = client.patch(f"/sections/{section.section_id}", json={"faculty_nuids": [f2.nuid]})
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
    response = client.patch(f"/sections/{section.section_id}", json={"faculty_nuids": [99999]})
    assert response.status_code == 400
    assert response.json()["detail"] == "FacultyNUIDs is invalid"


# ---------------------------------------------------------------------------
# DELETE /sections/{id}
# ---------------------------------------------------------------------------


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

    check = db_session.query(Section).filter(Section.section_id == section.section_id).first()
    assert check is None


def test_delete_section_not_found_returns_404(client, db_session):
    response = client.delete("/sections/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Section not found"


# ---------------------------------------------------------------------------
# PATCH /sections/{id} — lock enforcement
# ---------------------------------------------------------------------------


def test_patch_section_acquires_lock_automatically(client, db_session):
    """PATCH acquires the lock on behalf of the caller — no prior /lock call needed."""
    from app.core.auth import get_db_user
    from app.main import app
    from app.models.section_lock import SectionLock
    from app.models.user import User

    schedule, course, time_block = _seed_schedule_course_timeblock(db_session)
    section = Section(
        schedule_id=schedule.schedule_id,
        time_block_id=time_block.time_block_id,
        course_id=course.course_id,
        capacity=25,
        section_number=1,
    )
    db_session.add(section)
    db_session.flush()
    user = User(nuid=9001, first_name="Admin", last_name="User", email="a@test.com", role="ADMIN")
    db_session.add(user)
    db_session.commit()

    app.dependency_overrides[get_db_user] = lambda: user
    response = client.patch(f"/sections/{section.section_id}", json={"capacity": 30})

    assert response.status_code == 200
    lock = (
        db_session.query(SectionLock).filter(SectionLock.section_id == section.section_id).first()
    )
    assert lock is not None
    assert lock.locked_by == user.user_id


def test_patch_section_locked_by_other_user_returns_423(client, db_session):
    """PATCH returns 423 when another user currently holds the lock."""
    from datetime import UTC, datetime, timedelta

    from app.core.auth import get_db_user
    from app.main import app
    from app.models.section_lock import SectionLock
    from app.models.user import User

    schedule, course, time_block = _seed_schedule_course_timeblock(db_session)
    section = Section(
        schedule_id=schedule.schedule_id,
        time_block_id=time_block.time_block_id,
        course_id=course.course_id,
        capacity=25,
        section_number=1,
    )
    db_session.add(section)
    db_session.flush()
    owner = User(
        nuid=9001, first_name="Owner", last_name="User", email="owner@test.com", role="ADMIN"
    )
    caller = User(
        nuid=9002, first_name="Caller", last_name="User", email="caller@test.com", role="ADMIN"
    )
    db_session.add_all([owner, caller])
    db_session.commit()

    now = datetime.now(UTC).replace(tzinfo=None)
    db_session.add(
        SectionLock(
            section_id=section.section_id,
            locked_by=owner.user_id,
            expires_at=now + timedelta(minutes=2),
        )
    )
    db_session.commit()

    app.dependency_overrides[get_db_user] = lambda: caller
    response = client.patch(f"/sections/{section.section_id}", json={"capacity": 30})

    assert response.status_code == 423
    assert response.json()["detail"]["locked_by"] == owner.user_id
