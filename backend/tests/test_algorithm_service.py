"""Tests for algorithm service warning persistence and generation."""

from datetime import time
from unittest.mock import patch

from app.algorithms.models import CourseAssignment, TimeBlockAssignmentResult
from app.core.enums import WarningType
from app.models.campus import Campus
from app.models.course import Course
from app.models.faculty import Faculty
from app.models.schedule import Schedule
from app.models.schedule_warning import ScheduleWarning
from app.models.semester import Semester
from app.models.time_block import TimeBlock
from app.schemas.algorithm_params import AlgorithmParameters
from app.schemas.course import CourseResponse
from app.services.algorithm import _persist_warnings, _run_algorithm

# ---------------------------------------------------------------------------
# _persist_warnings — unit tests (no heavy seed needed)
# ---------------------------------------------------------------------------


def test_persist_warnings_creates_unmatched_rows(db_session):
    campus = Campus(name="Boston")
    db_session.add(campus)
    db_session.flush()
    semester = Semester(season="Fall", year=2090)
    db_session.add(semester)
    db_session.flush()
    schedule = Schedule(name="T", semester_id=semester.semester_id, campus=campus.campus_id)
    db_session.add(schedule)
    db_session.commit()

    unmatched = [CourseAssignment(section_id=1, course_id=42, is_matched=False, unmatched_reason="No qualified faculty")]
    _persist_warnings(db_session, schedule.schedule_id, [], unmatched)
    db_session.flush()

    rows = db_session.query(ScheduleWarning).filter(ScheduleWarning.schedule_id == schedule.schedule_id).all()
    assert len(rows) == 1
    assert rows[0].type == WarningType.INSUFFICIENT_FACULTY_SUPPLY.value
    assert rows[0].course_id == 42
    assert "No qualified faculty" in rows[0].message


def test_persist_warnings_skips_dismissed_unmatched(db_session):
    campus = Campus(name="Boston")
    db_session.add(campus)
    db_session.flush()
    semester = Semester(season="Fall", year=2091)
    db_session.add(semester)
    db_session.flush()
    schedule = Schedule(name="T", semester_id=semester.semester_id, campus=campus.campus_id)
    db_session.add(schedule)
    db_session.flush()

    # Seed a dismissed warning matching the unmatched key
    dismissed = ScheduleWarning(
        schedule_id=schedule.schedule_id,
        type=WarningType.INSUFFICIENT_FACULTY_SUPPLY.value,
        severity=str(WarningType.INSUFFICIENT_FACULTY_SUPPLY.severity.value),
        message="old",
        course_id=42,
        dismissed=True,
    )
    db_session.add(dismissed)
    db_session.commit()

    unmatched = [CourseAssignment(section_id=1, course_id=42, is_matched=False, unmatched_reason="No qualified faculty")]
    _persist_warnings(db_session, schedule.schedule_id, [], unmatched)
    db_session.flush()

    rows = db_session.query(ScheduleWarning).filter(ScheduleWarning.schedule_id == schedule.schedule_id).all()
    # Dismissed row survives; no new duplicate added
    assert len(rows) == 1
    assert rows[0].dismissed is True


def test_persist_warnings_replaces_non_dismissed_on_rerun(db_session):
    campus = Campus(name="Boston")
    db_session.add(campus)
    db_session.flush()
    semester = Semester(season="Fall", year=2092)
    db_session.add(semester)
    db_session.flush()
    schedule = Schedule(name="T", semester_id=semester.semester_id, campus=campus.campus_id)
    db_session.add(schedule)
    db_session.flush()

    old = ScheduleWarning(
        schedule_id=schedule.schedule_id,
        type=WarningType.INSUFFICIENT_FACULTY_SUPPLY.value,
        severity="2",
        message="stale",
        dismissed=False,
    )
    db_session.add(old)
    db_session.commit()

    _persist_warnings(db_session, schedule.schedule_id, [], [])
    db_session.flush()

    rows = db_session.query(ScheduleWarning).filter(ScheduleWarning.schedule_id == schedule.schedule_id).all()
    assert rows == []  # stale non-dismissed row was deleted


# ---------------------------------------------------------------------------
# _run_algorithm — integration with mocked Phase 1
# ---------------------------------------------------------------------------


def _seed_full(db):
    campus = Campus(name="Boston")
    db.add(campus)
    db.flush()
    semester = Semester(season="Fall", year=2093)
    db.add(semester)
    db.flush()
    schedule = Schedule(name="T", semester_id=semester.semester_id, campus=campus.campus_id)
    db.add(schedule)
    db.flush()
    course = Course(subject="CS", code=9999, name="CS 9999", description="", credits=4)
    db.add(course)
    db.flush()
    faculty = Faculty(
        nuid=99001,
        first_name="A",
        last_name="B",
        email="ab@test.edu",
        campus=campus.campus_id,
        active=True,
    )
    db.add(faculty)
    db.flush()
    tb = TimeBlock(meeting_days="MW", start_time=time(10, 0), end_time=time(11, 0), campus=campus.campus_id)
    db.add(tb)
    db.flush()
    db.commit()
    return schedule, course


def test_run_algorithm_creates_insufficient_faculty_warning_for_unmatched(db_session):
    schedule, course = _seed_full(db_session)

    fake_unmatched = CourseAssignment(
        section_id=1,
        course_id=course.course_id,
        is_matched=False,
        unmatched_reason="No faculty available",
    )
    fake_phase2 = TimeBlockAssignmentResult(assignments=[], warnings=[])

    dummy_course = CourseResponse(course_id=course.course_id, subject="CS", code=9999, name="CS 9999", description="", credits=4, section_count=1)
    with (
        patch("app.services.algorithm.semester_service.get_last_year", return_value=999),
        patch("app.services.algorithm.course_service.generate_course_list", return_value=[dummy_course]),
        patch("app.services.algorithm.match_courses_to_faculty", return_value=[fake_unmatched]),
        patch("app.services.algorithm.assign_time_blocks", return_value=fake_phase2),
    ):
        _run_algorithm(db_session, schedule.schedule_id, AlgorithmParameters())

    rows = (
        db_session.query(ScheduleWarning)
        .filter(
            ScheduleWarning.schedule_id == schedule.schedule_id,
            ScheduleWarning.type == WarningType.INSUFFICIENT_FACULTY_SUPPLY.value,
        )
        .all()
    )
    assert len(rows) == 1
    assert rows[0].course_id == course.course_id
    assert rows[0].severity == str(WarningType.INSUFFICIENT_FACULTY_SUPPLY.severity.value)
    assert "No faculty available" in rows[0].message
