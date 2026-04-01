"""
Tests for course service helpers and generate_course_list.
"""

from datetime import time

import pytest

from app.core.enums import PreferenceLevel
from app.models.campus import Campus
from app.models.course import Course
from app.models.course_preference import CoursePreference
from app.models.faculty import Faculty
from app.models.schedule import Schedule
from app.models.section import Section
from app.models.semester import Semester
from app.models.time_block import TimeBlock
from app.repositories import semester as semester_repo
from app.schemas.course import CourseResponse
from app.services import course as course_service

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_campus(db, name="Boston"):
    campus = Campus(name=name)
    db.add(campus)
    db.flush()
    return campus


def _make_semester(db, season="Fall", year=2025):
    semester = Semester(season=season, year=year)
    db.add(semester)
    db.flush()
    return semester


def _make_schedule(db, campus_id, semester_id, *, name="Test Schedule"):
    schedule = Schedule(name=name, semester_id=semester_id, campus=campus_id)
    db.add(schedule)
    db.commit()
    return schedule


def _make_course(db, priority=False, name="CS 1800", description="Discrete", credits=4):
    course = Course(
        name=name, description=description, credits=credits, priority=priority
    )
    db.add(course)
    db.flush()
    return course


def _make_time_block(db, campus_id):
    tb = TimeBlock(
        meeting_days="MWF",
        start_time=time(9, 0),
        end_time=time(10, 0),
        campus=campus_id,
    )
    db.add(tb)
    db.flush()
    return tb


def _make_section(db, schedule_id, course_id, time_block_id, section_number=1):
    section = Section(
        schedule_id=schedule_id,
        course_id=course_id,
        time_block_id=time_block_id,
        section_number=section_number,
        capacity=30,
    )
    db.add(section)
    db.flush()
    return section


def _make_faculty(db, campus_id, nuid=100001):
    faculty = Faculty(
        nuid=nuid,
        first_name="Test",
        last_name="Faculty",
        email=f"faculty{nuid}@test.edu",
        campus=campus_id,
    )
    db.add(faculty)
    db.flush()
    return faculty


def _make_preference(db, faculty_nuid, course_id, preference: PreferenceLevel):
    pref = CoursePreference(
        faculty_nuid=faculty_nuid,
        course_id=course_id,
        preference=preference,
    )
    db.add(pref)
    db.flush()
    return pref


# ---------------------------------------------------------------------------
# _course_to_response
# ---------------------------------------------------------------------------


class TestCourseToResponse:
    def test_course_subject_is_prefix(self, db_session):
        """CourseSubject should be 'CS', not '1800'."""
        course = _make_course(db_session, name="CS 1800")
        response = course_service._course_to_response(course, section_count=1)
        assert response.CourseSubject == "CS"

    def test_course_no_is_numeric_part(self, db_session):
        """CourseNo should be 1800 (int), not 'CS' (string)."""
        course = _make_course(db_session, name="CS 1800")
        response = course_service._course_to_response(course, section_count=1)
        assert response.CourseNo == 1800

    def test_course_no_is_int_not_string(self, db_session):
        course = _make_course(db_session, name="DS 3000")
        response = course_service._course_to_response(course, section_count=1)
        assert isinstance(response.CourseNo, int)

    def test_different_subject_prefix(self, db_session):
        """Works with DS and CY prefixes, not just CS."""
        course = _make_course(db_session, name="DS 4400")
        response = course_service._course_to_response(course, section_count=1)
        assert response.CourseSubject == "DS"
        assert response.CourseNo == 4400

    def test_section_count_preserved(self, db_session):
        course = _make_course(db_session, name="CS 2000")
        response = course_service._course_to_response(course, section_count=3)
        assert response.SectionCount == 3

    def test_priority_defaults_false(self, db_session):
        course = _make_course(db_session, name="CS 9999")
        response = course_service._course_to_response(course, section_count=1)
        assert response.Priority is False

    def test_priority_explicit_true(self, db_session):
        course = _make_course(db_session, name="CS 1800", priority=True)
        response = course_service._course_to_response(course, section_count=2)
        assert response.Priority is True

    def test_course_name_preserved(self, db_session):
        course = _make_course(db_session, name="CY 2550")
        response = course_service._course_to_response(course, section_count=1)
        assert response.CourseName == "CY 2550"

    def test_qualified_faculty_counts_pref_1_to_3_only(self, db_session):
        """EAGER(1), READY(2), WILLING(3) count; NOT_INTERESTED(4) does not."""
        campus = _make_campus(db_session)
        course = _make_course(db_session, name="CS 3000")
        f1 = _make_faculty(db_session, campus.campus_id, nuid=1)
        f2 = _make_faculty(db_session, campus.campus_id, nuid=2)
        f3 = _make_faculty(db_session, campus.campus_id, nuid=3)
        f4 = _make_faculty(db_session, campus.campus_id, nuid=4)
        _make_preference(db_session, f1.nuid, course.course_id, PreferenceLevel.EAGER)
        _make_preference(db_session, f2.nuid, course.course_id, PreferenceLevel.READY)
        _make_preference(db_session, f3.nuid, course.course_id, PreferenceLevel.WILLING)
        _make_preference(
            db_session, f4.nuid, course.course_id, PreferenceLevel.NOT_INTERESTED
        )
        db_session.refresh(course)
        response = course_service._course_to_response(course, section_count=1)
        assert response.QualifiedFaculty == 3

    def test_qualified_faculty_zero_when_no_preferences(self, db_session):
        course = _make_course(db_session, name="CS 4000")
        response = course_service._course_to_response(course, section_count=1)
        assert response.QualifiedFaculty == 0

    def test_not_interested_does_not_count(self, db_session):
        campus = _make_campus(db_session)
        course = _make_course(db_session, name="CS 5000")
        faculty = _make_faculty(db_session, campus.campus_id, nuid=10)
        _make_preference(
            db_session, faculty.nuid, course.course_id, PreferenceLevel.NOT_INTERESTED
        )
        db_session.refresh(course)
        response = course_service._course_to_response(course, section_count=1)
        assert response.QualifiedFaculty == 0


# ---------------------------------------------------------------------------
# sort_course_list
# ---------------------------------------------------------------------------


class TestSortCourseList:
    def _resp(self, course_id, priority, qualified_faculty, course_no):
        return CourseResponse(
            CourseID=course_id,
            Priority=priority,
            QualifiedFaculty=qualified_faculty,
            CourseNo=course_no,
            SectionCount=1,
        )

    def test_priority_courses_come_before_non_priority(self):
        non_priority = self._resp(
            1, priority=False, qualified_faculty=1, course_no=1000
        )
        priority = self._resp(2, priority=True, qualified_faculty=10, course_no=9999)
        result = course_service.sort_course_list([non_priority, priority])
        assert result[0].CourseID == 2

    def test_most_constrained_first_within_same_priority(self):
        """Fewest qualified faculty (most constrained) comes first."""
        constrained = self._resp(1, priority=True, qualified_faculty=1, course_no=2000)
        unconstrained = self._resp(
            2, priority=True, qualified_faculty=10, course_no=1000
        )
        result = course_service.sort_course_list([unconstrained, constrained])
        assert result[0].CourseID == 1

    def test_course_no_ascending_tiebreak(self):
        a = self._resp(1, priority=False, qualified_faculty=5, course_no=1000)
        b = self._resp(2, priority=False, qualified_faculty=5, course_no=2000)
        result = course_service.sort_course_list([b, a])
        assert result[0].CourseID == 1

    def test_full_ordering_priority_then_constrained_then_number(self):
        # priority=True, fewer faculty, higher number — first
        a = self._resp(1, priority=True, qualified_faculty=2, course_no=9000)
        # priority=True, more faculty, lower number — second
        b = self._resp(2, priority=True, qualified_faculty=8, course_no=1000)
        # priority=False, fewer faculty, lower number — third
        c = self._resp(3, priority=False, qualified_faculty=1, course_no=500)
        # priority=False, more faculty, higher number — fourth
        d = self._resp(4, priority=False, qualified_faculty=10, course_no=8000)
        result = course_service.sort_course_list([d, c, b, a])
        assert [r.CourseID for r in result] == [1, 2, 3, 4]

    def test_empty_list_returns_empty(self):
        assert course_service.sort_course_list([]) == []

    def test_single_element_unchanged(self):
        item = self._resp(1, priority=True, qualified_faculty=3, course_no=1000)
        result = course_service.sort_course_list([item])
        assert result[0].CourseID == 1

    def test_course_no_none_treated_as_zero(self):
        """None CourseNo sorts before any positive number (treated as 0)."""
        a = self._resp(1, priority=False, qualified_faculty=5, course_no=None)
        b = self._resp(2, priority=False, qualified_faculty=5, course_no=1000)
        result = course_service.sort_course_list([b, a])
        assert result[0].CourseID == 1

    def test_non_priority_never_precedes_priority_regardless_of_faculty(self):
        """Even a non-priority course with 0 faculty should rank after
        any priority course."""
        non_priority = self._resp(1, priority=False, qualified_faculty=0, course_no=1)
        priority = self._resp(2, priority=True, qualified_faculty=100, course_no=9999)
        result = course_service.sort_course_list([non_priority, priority])
        assert result[0].CourseID == 2


# ---------------------------------------------------------------------------
# get_section_count (service function)
# ---------------------------------------------------------------------------


class TestGetSectionCount:
    def test_section_count_read_from_schedule(self, db_session):
        campus = _make_campus(db_session)
        sem = _make_semester(db_session)
        schedule = _make_schedule(db_session, campus.campus_id, sem.semester_id)
        tb = _make_time_block(db_session, campus.campus_id)
        course = _make_course(db_session, name="CS 2100")
        _make_section(
            db_session,
            schedule.schedule_id,
            course.course_id,
            tb.time_block_id,
            section_number=1,
        )
        _make_section(
            db_session,
            schedule.schedule_id,
            course.course_id,
            tb.time_block_id,
            section_number=2,
        )
        db_session.refresh(schedule)

        result = course_service.get_section_count(schedule, [course], [])

        assert len(result) == 1
        assert result[0].SectionCount == 2

    def test_new_courses_default_to_one_section(self, db_session):
        campus = _make_campus(db_session)
        sem = _make_semester(db_session)
        schedule = _make_schedule(db_session, campus.campus_id, sem.semester_id)
        new_course = _make_course(db_session, name="CS 9001")
        db_session.refresh(schedule)

        result = course_service.get_section_count(schedule, [], [new_course])

        assert len(result) == 1
        assert result[0].SectionCount == 1

    def test_raises_when_existing_course_has_zero_sections(self, db_session):
        """A course listed as existing but absent from the schedule should
        raise ValueError."""
        campus = _make_campus(db_session)
        sem = _make_semester(db_session)
        schedule = _make_schedule(db_session, campus.campus_id, sem.semester_id)
        course = _make_course(db_session, name="CS 3200")
        db_session.refresh(schedule)

        with pytest.raises(ValueError):
            course_service.get_section_count(schedule, [course], [])

    def test_high_priority_flag_set_for_known_courses(self, db_session):
        campus = _make_campus(db_session)
        sem = _make_semester(db_session)
        schedule = _make_schedule(db_session, campus.campus_id, sem.semester_id)
        tb = _make_time_block(db_session, campus.campus_id)
        course = _make_course(db_session, name="CS 1800", priority=True)
        _make_section(
            db_session, schedule.schedule_id, course.course_id, tb.time_block_id
        )
        db_session.refresh(schedule)

        result = course_service.get_section_count(schedule, [course], [])

        assert result[0].Priority is True

    def test_non_priority_course_not_flagged(self, db_session):
        campus = _make_campus(db_session)
        sem = _make_semester(db_session)
        schedule = _make_schedule(db_session, campus.campus_id, sem.semester_id)
        tb = _make_time_block(db_session, campus.campus_id)
        course = _make_course(db_session, name="CS 9999")
        _make_section(
            db_session, schedule.schedule_id, course.course_id, tb.time_block_id
        )
        db_session.refresh(schedule)

        result = course_service.get_section_count(schedule, [course], [])

        assert result[0].Priority is False

    def test_all_high_priority_course_names_flagged(self, db_session):
        """Every name in HIGH_PRIORITY_COURSES should yield Priority=True."""
        campus = _make_campus(db_session)
        sem = _make_semester(db_session)
        schedule = _make_schedule(db_session, campus.campus_id, sem.semester_id)
        tb = _make_time_block(db_session, campus.campus_id)

        priority_courses = []
        for i, name in enumerate(course_service.HIGH_PRIORITY_COURSES):
            c = _make_course(db_session, name=name, priority=True)
            _make_section(
                db_session,
                schedule.schedule_id,
                c.course_id,
                tb.time_block_id,
                section_number=i + 1,
            )
            priority_courses.append(c)
        db_session.refresh(schedule)

        result = course_service.get_section_count(schedule, priority_courses, [])

        assert all(r.Priority is True for r in result)

    def test_new_courses_not_flagged_high_priority(self, db_session):
        """New courses always get Priority=False even if their name
        matches HIGH_PRIORITY_COURSES."""
        campus = _make_campus(db_session)
        sem = _make_semester(db_session)
        schedule = _make_schedule(db_session, campus.campus_id, sem.semester_id)
        new_course = _make_course(db_session, name="CS 1800")
        db_session.refresh(schedule)

        result = course_service.get_section_count(schedule, [], [new_course])

        assert result[0].Priority is False
        assert result[0].SectionCount == 1

    def test_combined_existing_and_new_courses(self, db_session):
        campus = _make_campus(db_session)
        sem = _make_semester(db_session)
        schedule = _make_schedule(db_session, campus.campus_id, sem.semester_id)
        tb = _make_time_block(db_session, campus.campus_id)
        existing = _make_course(db_session, name="CS 2000")
        new_course = _make_course(
            db_session, name="CS 9999", description="new", credits=3
        )
        _make_section(
            db_session, schedule.schedule_id, existing.course_id, tb.time_block_id
        )
        db_session.refresh(schedule)

        result = course_service.get_section_count(schedule, [existing], [new_course])

        assert len(result) == 2
        existing_resp = next(r for r in result if r.CourseName == "CS 2000")
        new_resp = next(r for r in result if r.CourseName == "CS 9999")
        assert existing_resp.SectionCount == 1
        assert new_resp.SectionCount == 1

    def test_multiple_sections_counted_correctly(self, db_session):
        campus = _make_campus(db_session)
        sem = _make_semester(db_session)
        schedule = _make_schedule(db_session, campus.campus_id, sem.semester_id)
        tb = _make_time_block(db_session, campus.campus_id)
        course = _make_course(db_session, name="CS 2800")
        for i in range(3):
            _make_section(
                db_session,
                schedule.schedule_id,
                course.course_id,
                tb.time_block_id,
                section_number=i + 1,
            )
        db_session.refresh(schedule)

        result = course_service.get_section_count(schedule, [course], [])

        assert result[0].SectionCount == 3


# ---------------------------------------------------------------------------
# semester_repo.get_last_year
# ---------------------------------------------------------------------------


class TestGetLastYear:
    """Tests the season-matched previous-year lookup used by the router."""

    def test_returns_same_season_previous_year(self, db_session):
        sem_25 = _make_semester(db_session, season="Fall", year=2025)
        sem_26 = _make_semester(db_session, season="Fall", year=2026)

        result = semester_repo.get_last_year(db_session, sem_26.semester_id)

        assert result == sem_25.semester_id

    def test_does_not_return_different_season(self, db_session):
        """Spring 2025 should NOT be returned for Fall 2026."""
        _make_semester(db_session, season="Spring", year=2025)
        sem_26 = _make_semester(db_session, season="Fall", year=2026)

        # No Fall 2025 exists — should return None and not error
        last_year = semester_repo.get_last_year(db_session, sem_26.semester_id)

        assert last_year is None

    def test_raises_when_no_previous_year_exists(self, db_session):
        sem_26 = _make_semester(db_session, season="Fall", year=2026)

        last_year = semester_repo.get_last_year(db_session, sem_26.semester_id)
        assert last_year is None

    def test_spring_to_spring(self, db_session):
        sem_25 = _make_semester(db_session, season="Spring", year=2025)
        sem_26 = _make_semester(db_session, season="Spring", year=2026)

        result = semester_repo.get_last_year(db_session, sem_26.semester_id)

        assert result == sem_25.semester_id


# ---------------------------------------------------------------------------
# generate_course_list
# ---------------------------------------------------------------------------


class TestGenerateCourseList:
    def test_returns_courses_from_given_semester_schedule(self, db_session):
        """generate_course_list receives the previous semester_id from the router."""
        campus = _make_campus(db_session)
        sem_prev = _make_semester(db_session, season="Fall", year=2025)
        schedule = _make_schedule(db_session, campus.campus_id, sem_prev.semester_id)
        tb = _make_time_block(db_session, campus.campus_id)
        course = _make_course(db_session, name="CS 2000")
        _make_section(
            db_session, schedule.schedule_id, course.course_id, tb.time_block_id
        )

        result = course_service.generate_course_list(
            db_session, sem_prev.semester_id, [], campus.campus_id
        )

        assert any(r.CourseName == "CS 2000" for r in result)

    def test_result_is_sorted_priority_first(self, db_session):
        campus = _make_campus(db_session)
        sem = _make_semester(db_session, season="Fall", year=2025)
        schedule = _make_schedule(db_session, campus.campus_id, sem.semester_id)
        tb = _make_time_block(db_session, campus.campus_id)

        priority_course = _make_course(db_session, name="CS 1800", priority=True)
        other_course = _make_course(
            db_session,
            name="CS 9999",
            description="d",
            credits=3,
        )
        _make_section(
            db_session,
            schedule.schedule_id,
            priority_course.course_id,
            tb.time_block_id,
            section_number=1,
        )
        _make_section(
            db_session,
            schedule.schedule_id,
            other_course.course_id,
            tb.time_block_id,
            section_number=2,
        )

        result = course_service.generate_course_list(
            db_session, sem.semester_id, [], campus.campus_id
        )

        assert result[0].Priority is True
        assert result[0].CourseName == "CS 1800"

    def test_new_course_ids_included_with_one_section(self, db_session):
        campus = _make_campus(db_session)
        sem = _make_semester(db_session, season="Fall", year=2025)
        schedule = _make_schedule(db_session, campus.campus_id, sem.semester_id)
        tb = _make_time_block(db_session, campus.campus_id)

        existing = _make_course(db_session, name="CS 2000")
        new_course = _make_course(
            db_session, name="CS 8888", description="New", credits=3
        )
        _make_section(
            db_session, schedule.schedule_id, existing.course_id, tb.time_block_id
        )

        result = course_service.generate_course_list(
            db_session, sem.semester_id, [new_course.course_id], campus.campus_id
        )

        new_resp = next((r for r in result if r.CourseName == "CS 8888"), None)
        assert new_resp is not None
        assert new_resp.SectionCount == 1

    def test_raises_when_multiple_schedules_for_semester(self, db_session):
        campus = _make_campus(db_session)
        sem = _make_semester(db_session, season="Fall", year=2025)
        _make_schedule(db_session, campus.campus_id, sem.semester_id, name="S1")
        _make_schedule(db_session, campus.campus_id, sem.semester_id, name="S2")

        with pytest.raises(ValueError, match="Multiple"):
            course_service.generate_course_list(
                db_session, sem.semester_id, [], campus.campus_id
            )

    def test_raises_when_schedule_has_no_courses(self, db_session):
        campus = _make_campus(db_session)
        sem = _make_semester(db_session, season="Fall", year=2025)
        _make_schedule(db_session, campus.campus_id, sem.semester_id)

        with pytest.raises(ValueError):
            course_service.generate_course_list(
                db_session, sem.semester_id, [], campus.campus_id
            )

    def test_multiple_sections_preserved(self, db_session):
        """A course with 3 sections in the prior schedule should show SectionCount=3."""
        campus = _make_campus(db_session)
        sem = _make_semester(db_session, season="Fall", year=2025)
        schedule = _make_schedule(db_session, campus.campus_id, sem.semester_id)
        tb = _make_time_block(db_session, campus.campus_id)
        course = _make_course(db_session, name="CS 2800")
        for i in range(3):
            _make_section(
                db_session,
                schedule.schedule_id,
                course.course_id,
                tb.time_block_id,
                section_number=i + 1,
            )

        result = course_service.generate_course_list(
            db_session, sem.semester_id, [], campus.campus_id
        )

        assert result[0].SectionCount == 3

    def test_sorted_by_constraint_within_non_priority_group(self, db_session):
        """Within non-priority courses, fewest qualified faculty comes first."""
        campus = _make_campus(db_session)
        sem = _make_semester(db_session, season="Fall", year=2025)
        schedule = _make_schedule(db_session, campus.campus_id, sem.semester_id)
        tb = _make_time_block(db_session, campus.campus_id)

        constrained = _make_course(
            db_session, name="CS 7000", description="d", credits=3
        )
        unconstrained = _make_course(
            db_session, name="CS 8000", description="d", credits=3
        )
        _make_section(
            db_session,
            schedule.schedule_id,
            constrained.course_id,
            tb.time_block_id,
            section_number=1,
        )
        _make_section(
            db_session,
            schedule.schedule_id,
            unconstrained.course_id,
            tb.time_block_id,
            section_number=2,
        )

        f1 = _make_faculty(db_session, campus.campus_id, nuid=501)
        f2 = _make_faculty(db_session, campus.campus_id, nuid=502)
        f3 = _make_faculty(db_session, campus.campus_id, nuid=503)
        f4 = _make_faculty(db_session, campus.campus_id, nuid=504)
        f5 = _make_faculty(db_session, campus.campus_id, nuid=505)
        f6 = _make_faculty(db_session, campus.campus_id, nuid=506)

        # constrained: 1 qualified faculty
        _make_preference(
            db_session, f1.nuid, constrained.course_id, PreferenceLevel.EAGER
        )
        # unconstrained: 5 qualified faculty
        for f in [f2, f3, f4, f5, f6]:
            _make_preference(
                db_session, f.nuid, unconstrained.course_id, PreferenceLevel.EAGER
            )

        result = course_service.generate_course_list(
            db_session, sem.semester_id, [], campus.campus_id
        )

        non_priority = [r for r in result if not r.Priority]
        assert non_priority[0].CourseName == "CS 7000"

    def test_with_schedule_id_path(self, db_session):
        """When schedule_id is provided, courses are read from that
        specific schedule."""
        campus = _make_campus(db_session)
        sem = _make_semester(db_session, season="Fall", year=2025)
        schedule = _make_schedule(db_session, campus.campus_id, sem.semester_id)
        tb = _make_time_block(db_session, campus.campus_id)
        course = _make_course(db_session, name="CS 3100")
        _make_section(
            db_session, schedule.schedule_id, course.course_id, tb.time_block_id
        )

        result = course_service.generate_course_list(
            db_session, sem.semester_id, [], campus.campus_id
        )

        assert any(r.CourseName == "CS 3100" for r in result)

    def test_empty_new_course_ids_list_works(self, db_session):
        campus = _make_campus(db_session)
        sem = _make_semester(db_session, season="Fall", year=2025)
        schedule = _make_schedule(db_session, campus.campus_id, sem.semester_id)
        tb = _make_time_block(db_session, campus.campus_id)
        course = _make_course(db_session, name="CS 2700")
        _make_section(
            db_session, schedule.schedule_id, course.course_id, tb.time_block_id
        )

        result = course_service.generate_course_list(
            db_session, sem.semester_id, [], campus.campus_id
        )

        assert len(result) == 1
