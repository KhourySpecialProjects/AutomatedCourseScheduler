"""Unit/integration tests for section service — update_section and error_check."""

from datetime import time

import pytest

from app.core.enums import PreferenceLevel, WarningType
from app.models import (
    Course,
    CoursePreference,
    Faculty,
    FacultyAssignment,
    MeetingPreference,
    Schedule,
    Section,
    TimeBlock,
)
from app.models.campus import Campus as CampusModel
from app.models.semester import Semester as SemesterModel
from app.schemas.section import SectionUpdate
from app.services import section as section_service

# ---------------------------------------------------------------------------
# Shared helpers
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


def _make_schedule(db, campus, semester, name="F24"):
    schedule = Schedule(name=name, semester_id=semester.semester_id, campus=campus.campus_id)
    db.add(schedule)
    db.flush()
    return schedule


def _make_course(
    db,
    name="Fundamentals of Computer Science I",
    subject="CS",
    code=2500,
    description="Intro",
    credits=4,
):
    course = Course(name=name, subject=subject, code=code, description=description, credits=credits)
    db.add(course)
    db.flush()
    return course


def _make_time_block(db, campus, days="MW", start_h=10, end_h=11):
    tb = TimeBlock(
        meeting_days=days,
        start_time=time(start_h, 0),
        end_time=time(end_h, 0),
        campus=campus.campus_id,
    )
    db.add(tb)
    db.flush()
    return tb


def _make_faculty(db, campus, nuid, email, max_load=3):
    f = Faculty(
        nuid=nuid,
        first_name="Test",
        last_name="Faculty",
        email=email,
        campus=campus.campus_id,
        max_load=max_load,
    )
    db.add(f)
    db.flush()
    return f


def _make_section(db, schedule, course, time_block, number=1, capacity=30):
    s = Section(
        schedule_id=schedule.schedule_id,
        time_block_id=time_block.time_block_id,
        course_id=course.course_id,
        section_number=number,
        capacity=capacity,
    )
    db.add(s)
    db.flush()
    return s


# ---------------------------------------------------------------------------
# error_check — no updates triggers no warnings
# ---------------------------------------------------------------------------


def test_error_check_empty_update_returns_no_warnings(db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course = _make_course(db_session)
    tb = _make_time_block(db_session, campus)
    section = _make_section(db_session, schedule, course, tb)
    db_session.commit()

    updates = SectionUpdate()  # no fields set
    warnings = section_service.error_check(db_session, section, updates)

    assert warnings == []


# ---------------------------------------------------------------------------
# error_check — time_block_id update
# ---------------------------------------------------------------------------


def test_error_check_time_block_overload_warning(db_session):
    """2 CS sections both landing in tb_b → 2/2 = 100% in that block → overload."""
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course = _make_course(db_session, name="CS 2500")
    tb_a = _make_time_block(db_session, campus, start_h=10, end_h=11)
    tb_b = _make_time_block(db_session, campus, start_h=12, end_h=13)
    # Another section already in tb_b; moving section to tb_b gives 2/2 = 100%
    _make_section(db_session, schedule, course, tb_b, number=1)
    section = _make_section(db_session, schedule, course, tb_a, number=2)
    db_session.commit()

    # Simulate the field update already applied to the ORM object
    section.time_block_id = tb_b.time_block_id
    updates = SectionUpdate(time_block_id=tb_b.time_block_id)

    warnings = section_service.error_check(db_session, section, updates)

    assert WarningType.TIME_BLOCK_OVERLOAD in warnings


def test_error_check_no_time_block_overload_below_threshold(db_session):
    """8 CS sections; updating one to a new block makes it 1/8 = 12.5% < 15%."""
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course = _make_course(db_session, name="CS 2500")
    db_session.commit()

    # 9 time blocks: tb[0]–tb[7] for the existing sections, tb[8] for the target
    time_blocks = [_make_time_block(db_session, campus, start_h=8 + i, end_h=9 + i) for i in range(9)]
    db_session.flush()

    sections = []
    for i in range(8):
        s = _make_section(db_session, schedule, course, time_blocks[i], number=i + 1)
        sections.append(s)
    db_session.commit()

    target = sections[0]
    target.time_block_id = time_blocks[8].time_block_id
    updates = SectionUpdate(time_block_id=time_blocks[8].time_block_id)

    warnings = section_service.error_check(db_session, target, updates)

    assert WarningType.TIME_BLOCK_OVERLOAD not in warnings


def test_error_check_unpreferenced_time_warning(db_session):
    """Faculty assigned to section has no meeting preference for the new time block."""
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course = _make_course(db_session)
    tb_a = _make_time_block(db_session, campus, start_h=10, end_h=11)
    tb_b = _make_time_block(db_session, campus, start_h=14, end_h=15)
    faculty = _make_faculty(db_session, campus, nuid=1001, email="f1@test.edu")
    section = _make_section(db_session, schedule, course, tb_a)
    db_session.add(FacultyAssignment(faculty_nuid=faculty.nuid, section_id=section.section_id))
    # No MeetingPreference for tb_b
    db_session.commit()

    section.time_block_id = tb_b.time_block_id
    updates = SectionUpdate(time_block_id=tb_b.time_block_id)

    warnings = section_service.error_check(db_session, section, updates)

    assert WarningType.UNPREFERENCED_TIME in warnings


def test_error_check_faculty_has_time_preference_no_warning(db_session):
    """Faculty has a positive meeting preference for the new time block — no warning."""
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course = _make_course(db_session)
    tb_a = _make_time_block(db_session, campus, start_h=10, end_h=11)
    tb_b = _make_time_block(db_session, campus, start_h=14, end_h=15)
    faculty = _make_faculty(db_session, campus, nuid=1001, email="f1@test.edu")
    section = _make_section(db_session, schedule, course, tb_a)
    db_session.add(FacultyAssignment(faculty_nuid=faculty.nuid, section_id=section.section_id))
    db_session.add(
        MeetingPreference(
            faculty_nuid=faculty.nuid,
            meeting_time=tb_b.time_block_id,
            preference=PreferenceLevel.READY,
        )
    )
    db_session.commit()

    section.time_block_id = tb_b.time_block_id
    updates = SectionUpdate(time_block_id=tb_b.time_block_id)

    warnings = section_service.error_check(db_session, section, updates)

    assert WarningType.UNPREFERENCED_TIME not in warnings


def test_error_check_not_interested_time_preference_counts_as_warning(db_session):
    """NOT_INTERESTED preference is treated the same as no preference."""
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course = _make_course(db_session)
    tb_a = _make_time_block(db_session, campus, start_h=10, end_h=11)
    tb_b = _make_time_block(db_session, campus, start_h=14, end_h=15)
    faculty = _make_faculty(db_session, campus, nuid=1001, email="f1@test.edu")
    section = _make_section(db_session, schedule, course, tb_a)
    db_session.add(FacultyAssignment(faculty_nuid=faculty.nuid, section_id=section.section_id))
    db_session.add(
        MeetingPreference(
            faculty_nuid=faculty.nuid,
            meeting_time=tb_b.time_block_id,
            preference=PreferenceLevel.NOT_INTERESTED,
        )
    )
    db_session.commit()

    section.time_block_id = tb_b.time_block_id
    updates = SectionUpdate(time_block_id=tb_b.time_block_id)

    warnings = section_service.error_check(db_session, section, updates)

    assert WarningType.UNPREFERENCED_TIME in warnings


# ---------------------------------------------------------------------------
# error_check — course_id update
# ---------------------------------------------------------------------------


def test_error_check_unpreferenced_course_warning(db_session):
    """Faculty assigned to section has no preference for the new course."""
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course_a = _make_course(db_session, name="CS 2500", code=2500)
    course_b = _make_course(db_session, name="CS 3500", code=3500)
    tb = _make_time_block(db_session, campus)
    faculty = _make_faculty(db_session, campus, nuid=1001, email="f1@test.edu")
    section = _make_section(db_session, schedule, course_a, tb)
    db_session.add(FacultyAssignment(faculty_nuid=faculty.nuid, section_id=section.section_id))
    # No CoursePreference for course_b
    db_session.commit()

    section.course_id = course_b.course_id
    updates = SectionUpdate(course_id=course_b.course_id)

    warnings = section_service.error_check(db_session, section, updates)

    assert WarningType.UNPREFERENCED_COURSE in warnings


def test_error_check_faculty_has_course_preference_no_warning(db_session):
    """Faculty has a positive course preference for the new course — no warning."""
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course_a = _make_course(db_session, name="CS 2500", code=2500)
    course_b = _make_course(db_session, name="CS 3500", code=3500)
    tb = _make_time_block(db_session, campus)
    faculty = _make_faculty(db_session, campus, nuid=1001, email="f1@test.edu")
    section = _make_section(db_session, schedule, course_a, tb)
    db_session.add(FacultyAssignment(faculty_nuid=faculty.nuid, section_id=section.section_id))
    db_session.add(
        CoursePreference(
            faculty_nuid=faculty.nuid,
            course_id=course_b.course_id,
            preference=PreferenceLevel.EAGER,
        )
    )
    db_session.commit()

    section.course_id = course_b.course_id
    updates = SectionUpdate(course_id=course_b.course_id)

    warnings = section_service.error_check(db_session, section, updates)

    assert WarningType.UNPREFERENCED_COURSE not in warnings


def test_error_check_not_interested_course_preference_counts_as_warning(db_session):
    """NOT_INTERESTED course preference is treated the same as no preference."""
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course_a = _make_course(db_session, name="CS 2500", code=2500)
    course_b = _make_course(db_session, name="CS 3500", code=3500)
    tb = _make_time_block(db_session, campus)
    faculty = _make_faculty(db_session, campus, nuid=1001, email="f1@test.edu")
    section = _make_section(db_session, schedule, course_a, tb)
    db_session.add(FacultyAssignment(faculty_nuid=faculty.nuid, section_id=section.section_id))
    db_session.add(
        CoursePreference(
            faculty_nuid=faculty.nuid,
            course_id=course_b.course_id,
            preference=PreferenceLevel.NOT_INTERESTED,
        )
    )
    db_session.commit()

    section.course_id = course_b.course_id
    updates = SectionUpdate(course_id=course_b.course_id)

    warnings = section_service.error_check(db_session, section, updates)

    assert WarningType.UNPREFERENCED_COURSE in warnings


# ---------------------------------------------------------------------------
# error_check — faculty_nuids update
# ---------------------------------------------------------------------------


def test_error_check_faculty_overload_warning(db_session):
    """Assigning a faculty already at max_load triggers FACULTY_OVERLOAD."""
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course = _make_course(db_session)
    tb = _make_time_block(db_session, campus)
    # Faculty with max_load=1 already has 1 assignment
    faculty = _make_faculty(db_session, campus, nuid=1001, email="f1@test.edu", max_load=1)
    other_section = _make_section(db_session, schedule, course, tb, number=1)
    db_session.add(FacultyAssignment(faculty_nuid=faculty.nuid, section_id=other_section.section_id))
    section = _make_section(db_session, schedule, course, tb, number=2)
    db_session.add(FacultyAssignment(faculty_nuid=faculty.nuid, section_id=section.section_id))
    db_session.commit()

    updates = SectionUpdate(faculty_nuids=[faculty.nuid])

    warnings = section_service.error_check(db_session, section, updates)

    assert WarningType.FACULTY_OVERLOAD in warnings


def test_error_check_faculty_within_max_load_no_warning(db_session):
    """Faculty below max_load does not trigger FACULTY_OVERLOAD."""
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course = _make_course(db_session)
    tb = _make_time_block(db_session, campus)
    # Faculty with max_load=3 has 0 existing assignments
    faculty = _make_faculty(db_session, campus, nuid=1001, email="f1@test.edu", max_load=3)
    section = _make_section(db_session, schedule, course, tb)
    db_session.commit()

    updates = SectionUpdate(faculty_nuids=[faculty.nuid])

    warnings = section_service.error_check(db_session, section, updates)

    assert WarningType.FACULTY_OVERLOAD not in warnings


def test_error_check_empty_faculty_nuids_no_warning(db_session):
    """Clearing all faculty assignments never triggers FACULTY_OVERLOAD."""
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course = _make_course(db_session)
    tb = _make_time_block(db_session, campus)
    section = _make_section(db_session, schedule, course, tb)
    db_session.commit()

    updates = SectionUpdate(faculty_nuids=[])

    warnings = section_service.error_check(db_session, section, updates)

    assert WarningType.FACULTY_OVERLOAD not in warnings


def test_error_check_crosslisted_sections_not_double_booked(db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course = _make_course(db_session, name="CS 2500", code=2500)
    tb = _make_time_block(db_session, campus)
    faculty = _make_faculty(db_session, campus, nuid=1001, email="f1@test.edu")

    a = _make_section(db_session, schedule, course, tb, number=1)
    b = _make_section(db_session, schedule, course, tb, number=2)
    # Crosslist them as partners.
    a.crosslisted_section_id = b.section_id
    b.crosslisted_section_id = a.section_id

    db_session.add(FacultyAssignment(faculty_nuid=faculty.nuid, section_id=a.section_id))
    db_session.add(FacultyAssignment(faculty_nuid=faculty.nuid, section_id=b.section_id))
    db_session.commit()

    warnings_a = section_service.error_check(db_session, a, SectionUpdate(faculty_nuids=[faculty.nuid]))
    warnings_b = section_service.error_check(db_session, b, SectionUpdate(faculty_nuids=[faculty.nuid]))

    assert WarningType.FACULTY_DOUBLE_BOOKED not in warnings_a
    assert WarningType.FACULTY_DOUBLE_BOOKED not in warnings_b

    # A third, non-crosslisted section at the same time block should still trigger a real double-booking warning.
    c = _make_section(db_session, schedule, course, tb, number=3)
    db_session.add(FacultyAssignment(faculty_nuid=faculty.nuid, section_id=c.section_id))
    db_session.commit()

    warnings_c = section_service.error_check(db_session, c, SectionUpdate(faculty_nuids=[faculty.nuid]))
    assert WarningType.FACULTY_DOUBLE_BOOKED in warnings_c


# ---------------------------------------------------------------------------
# update_section — basic behavior
# ---------------------------------------------------------------------------


def test_update_section_not_found_returns_none(db_session):
    result = section_service.update_section(db_session, 99999, SectionUpdate())
    assert result is None


def test_update_section_returns_dict_with_updated_and_warnings_keys(db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course = _make_course(db_session)
    tb = _make_time_block(db_session, campus)
    section = _make_section(db_session, schedule, course, tb)
    db_session.commit()

    result = section_service.update_section(db_session, section.section_id, SectionUpdate(capacity=99))

    assert result is not None
    assert "updated" in result
    assert "warnings" in result


def test_update_section_applies_capacity_change(db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course = _make_course(db_session)
    tb = _make_time_block(db_session, campus)
    section = _make_section(db_session, schedule, course, tb, capacity=30)
    db_session.commit()

    result = section_service.update_section(db_session, section.section_id, SectionUpdate(capacity=50))

    assert result["updated"].capacity == 50


def test_update_section_applies_room_change(db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course = _make_course(db_session)
    tb = _make_time_block(db_session, campus)
    section = _make_section(db_session, schedule, course, tb)
    db_session.commit()

    result = section_service.update_section(db_session, section.section_id, SectionUpdate(room="WVH108"))

    assert result["updated"].room == "WVH108"


def test_update_section_empty_warnings_on_simple_update(db_session):
    """Updating only capacity (no warning triggers) should return an empty warnings list."""
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course = _make_course(db_session)
    tb = _make_time_block(db_session, campus)
    section = _make_section(db_session, schedule, course, tb)
    db_session.commit()

    result = section_service.update_section(db_session, section.section_id, SectionUpdate(capacity=40))

    assert result["warnings"] == []


def test_update_section_raises_on_invalid_time_block(db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course = _make_course(db_session)
    tb = _make_time_block(db_session, campus)
    section = _make_section(db_session, schedule, course, tb)
    db_session.commit()

    with pytest.raises(ValueError, match="TimeBlockID is invalid"):
        section_service.update_section(db_session, section.section_id, SectionUpdate(time_block_id=99999))


def test_update_section_raises_on_invalid_course(db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course = _make_course(db_session)
    tb = _make_time_block(db_session, campus)
    section = _make_section(db_session, schedule, course, tb)
    db_session.commit()

    with pytest.raises(ValueError, match="CourseID is invalid"):
        section_service.update_section(db_session, section.section_id, SectionUpdate(course_id=99999))


def test_update_section_raises_on_self_crosslist(db_session):
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course = _make_course(db_session)
    tb = _make_time_block(db_session, campus)
    section = _make_section(db_session, schedule, course, tb)
    db_session.commit()

    with pytest.raises(ValueError, match="CrosslistedSectionID is invalid"):
        section_service.update_section(
            db_session,
            section.section_id,
            SectionUpdate(crosslisted_section_id=section.section_id),
        )


# ---------------------------------------------------------------------------
# update_section — warnings returned alongside the save
# ---------------------------------------------------------------------------


def test_update_section_returns_faculty_overload_warning_and_saves(db_session):
    """Even when FACULTY_OVERLOAD is detected, the section is still saved."""
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course = _make_course(db_session)
    tb = _make_time_block(db_session, campus)

    faculty = _make_faculty(db_session, campus, nuid=1001, email="f1@test.edu", max_load=1)
    other_section = _make_section(db_session, schedule, course, tb, number=1)
    db_session.add(FacultyAssignment(faculty_nuid=faculty.nuid, section_id=other_section.section_id))
    section = _make_section(db_session, schedule, course, tb, number=2)
    db_session.commit()

    result = section_service.update_section(db_session, section.section_id, SectionUpdate(faculty_nuids=[faculty.nuid]))

    assert result is not None
    assert WarningType.FACULTY_OVERLOAD in result["warnings"]
    assert result["updated"] is not None


def test_update_section_returns_unpreferenced_course_warning(db_session):
    """Changing course to one a faculty member is uninterested in returns UNPREFERENCED_COURSE."""
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course_a = _make_course(db_session, name="CS 2500", code=2500)
    course_b = _make_course(db_session, name="CS 3500", code=3500)
    tb = _make_time_block(db_session, campus)
    faculty = _make_faculty(db_session, campus, nuid=1001, email="f1@test.edu")
    section = _make_section(db_session, schedule, course_a, tb)
    db_session.add(FacultyAssignment(faculty_nuid=faculty.nuid, section_id=section.section_id))
    db_session.commit()

    result = section_service.update_section(db_session, section.section_id, SectionUpdate(course_id=course_b.course_id))

    assert WarningType.UNPREFERENCED_COURSE in result["warnings"]
    assert result["updated"].course_id == course_b.course_id


def test_update_section_no_warnings_when_faculty_prefers_new_course(db_session):
    """No UNPREFERENCED_COURSE when faculty has a positive preference."""
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course_a = _make_course(db_session, name="CS 2500", code=2500)
    course_b = _make_course(db_session, name="CS 3500", code=3500)
    tb = _make_time_block(db_session, campus)
    faculty = _make_faculty(db_session, campus, nuid=1001, email="f1@test.edu")
    section = _make_section(db_session, schedule, course_a, tb)
    db_session.add(FacultyAssignment(faculty_nuid=faculty.nuid, section_id=section.section_id))
    db_session.add(
        CoursePreference(
            faculty_nuid=faculty.nuid,
            course_id=course_b.course_id,
            preference=PreferenceLevel.WILLING,
        )
    )
    db_session.commit()

    result = section_service.update_section(db_session, section.section_id, SectionUpdate(course_id=course_b.course_id))

    assert WarningType.UNPREFERENCED_COURSE not in result["warnings"]


def test_update_section_returns_unpreferenced_time_warning(db_session):
    """Changing time block to one a faculty member has no preference
    for returns UNPREFERENCED_TIME."""
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course = _make_course(db_session, name="CS 2500")
    tb_a = _make_time_block(db_session, campus, start_h=10, end_h=11)
    tb_b = _make_time_block(db_session, campus, start_h=14, end_h=15)
    faculty = _make_faculty(db_session, campus, nuid=1001, email="f1@test.edu")
    section = _make_section(db_session, schedule, course, tb_a)
    db_session.add(FacultyAssignment(faculty_nuid=faculty.nuid, section_id=section.section_id))
    db_session.commit()

    result = section_service.update_section(db_session, section.section_id, SectionUpdate(time_block_id=tb_b.time_block_id))

    assert WarningType.UNPREFERENCED_TIME in result["warnings"]


def test_update_section_multiple_warnings_returned_together(db_session):
    """Both UNPREFERENCED_TIME and TIME_BLOCK_OVERLOAD can appear in the same result."""
    campus = _make_campus(db_session)
    semester = _make_semester(db_session)
    schedule = _make_schedule(db_session, campus, semester)
    course = _make_course(db_session, name="CS 2500")
    tb_a = _make_time_block(db_session, campus, start_h=10, end_h=11)
    tb_b = _make_time_block(db_session, campus, start_h=14, end_h=15)
    faculty = _make_faculty(db_session, campus, nuid=1001, email="f1@test.edu")
    # A section already in tb_b: moving section there gives 2/2 = 100% → overload
    _make_section(db_session, schedule, course, tb_b, number=1)
    section = _make_section(db_session, schedule, course, tb_a, number=2)
    db_session.add(FacultyAssignment(faculty_nuid=faculty.nuid, section_id=section.section_id))
    # No time preference for tb_b
    db_session.commit()

    result = section_service.update_section(db_session, section.section_id, SectionUpdate(time_block_id=tb_b.time_block_id))

    assert WarningType.TIME_BLOCK_OVERLOAD in result["warnings"]
    assert WarningType.UNPREFERENCED_TIME in result["warnings"]
