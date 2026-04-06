from datetime import time

from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.models import Course, Schedule, Section, TimeBlock
from app.models.campus import Campus as CampusModel
from app.models.section_lock import SectionLock
from app.models.semester import Semester as SemesterModel
from app.models.user import User

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


def _make_user(db, nuid=1):
    user = User(
        nuid=nuid,
        first_name="Test",
        last_name="User",
        email=f"user{nuid}@example.com",
        phone_number="1234567890",
        role="Admin",
    )
    db.add(user)
    db.flush()
    return user


def _make_section(db, season="Fall"):
    campus = _make_campus(db)
    semester = _make_semester(db, season=season)
    schedule = Schedule(
        name="F24", semester_id=semester.semester_id, campus=campus.campus_id
    )
    course = Course(name="CS 2500", description="Fundamentals", credits=4)
    db.add_all([schedule, course])
    db.flush()
    time_block = TimeBlock(
        meeting_days="MW",
        start_time=time(10, 0),
        end_time=time(11, 0),
        campus=campus.campus_id,
    )
    db.add(time_block)
    db.flush()
    section = Section(
        schedule_id=schedule.schedule_id,
        time_block_id=time_block.time_block_id,
        course_id=course.course_id,
        section_number=1,
        capacity=30,
    )
    db.add(section)
    db.commit()
    return section


# ---------------------------------------------------------------------------
# POST /sections/{id}/lock
# ---------------------------------------------------------------------------


def test_lock_success(client: TestClient, db_session: Session) -> None:
    user = _make_user(db_session)
    section = _make_section(db_session)
    response = client.post(f"/sections/{section.section_id}/lock?user_id={user.nuid}")
    assert response.status_code == 200
    data = response.json()
    assert data["section_id"] == section.section_id
    assert data["locked_by"] == user.nuid
    assert "expires_at" in data


def test_lock_same_user(client: TestClient, db_session: Session) -> None:
    user = _make_user(db_session)
    section = _make_section(db_session)
    response1 = client.post(f"/sections/{section.section_id}/lock?user_id={user.nuid}")
    response2 = client.post(f"/sections/{section.section_id}/lock?user_id={user.nuid}")
    assert response2.status_code == 200
    assert response2.json()["expires_at"] >= response1.json()["expires_at"]


def test_lock_different_user(client: TestClient, db_session: Session) -> None:
    user1 = _make_user(db_session, nuid=1)
    user2 = _make_user(db_session, nuid=2)
    section = _make_section(db_session)
    client.post(f"/sections/{section.section_id}/lock?user_id={user1.nuid}")
    response = client.post(f"/sections/{section.section_id}/lock?user_id={user2.nuid}")
    assert response.status_code == 423
    data = response.json()["detail"]
    assert data["locked_by"] == user1.nuid
    assert "expires_at" in data


def test_previous_lock_releases(client: TestClient, db_session: Session) -> None:
    user = _make_user(db_session)
    section1 = _make_section(db_session)
    section2 = _make_section(db_session, season="Spring")
    client.post(f"/sections/{section1.section_id}/lock?user_id={user.nuid}")
    client.post(f"/sections/{section2.section_id}/lock?user_id={user.nuid}")
    lock = (
        db_session.query(SectionLock)
        .filter(SectionLock.section_id == section1.section_id)
        .first()
    )
    assert lock is None


# ---------------------------------------------------------------------------
# POST /sections/{id}/unlock
# ---------------------------------------------------------------------------


def test_unlock_success(client: TestClient, db_session: Session) -> None:
    user = _make_user(db_session)
    section = _make_section(db_session)
    client.post(f"/sections/{section.section_id}/lock?user_id={user.nuid}")
    client.post(f"/sections/{section.section_id}/unlock?user_id={user.nuid}")
    lock = (
        db_session.query(SectionLock)
        .filter(SectionLock.section_id == section.section_id)
        .first()
    )
    assert lock is None


def test_unlock_lock_with_different_owner(
    client: TestClient, db_session: Session
) -> None:
    user1 = _make_user(db_session, nuid=1)
    user2 = _make_user(db_session, nuid=2)
    section = _make_section(db_session)
    client.post(f"/sections/{section.section_id}/lock?user_id={user1.nuid}")
    response = client.post(
        f"/sections/{section.section_id}/unlock?user_id={user2.nuid}"
    )
    assert response.status_code == 403


def test_unlock_section_with_no_lock(client: TestClient, db_session: Session) -> None:
    user = _make_user(db_session, nuid=1)
    section = _make_section(db_session)
    response = client.post(f"/sections/{section.section_id}/unlock?user_id={user.nuid}")
    assert response.status_code == 403
