"""Tests for faculty router: GET /faculty and GET /faculty/{id}."""

from datetime import time
from unittest.mock import MagicMock, patch

from app.core.enums import PreferenceLevel
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
from app.services import faculty as faculty_service


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


def _make_time_block(db, campus_id):
    tb = TimeBlock(
        meeting_days="MW",
        start_time=time(10, 0),
        end_time=time(11, 0),
        campus=campus_id,
    )
    db.add(tb)
    db.flush()
    return tb


def test_get_faculty_empty(client, db_session):
    response = client.get("/faculty")
    assert response.status_code == 200
    assert response.json() == []


def test_get_faculty_returns_all(client, db_session):
    db_session.add_all(
        [
            Faculty(
                nuid=1001,
                first_name="Jane",
                last_name="Doe",
                email="jane@example.com",
                campus="Boston",
            ),
            Faculty(
                nuid=1002,
                first_name="John",
                last_name="Smith",
                email="john@example.com",
                campus="Boston",
            ),
        ]
    )
    db_session.commit()

    response = client.get("/faculty")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_faculty_filter_by_campus(client, db_session):
    db_session.add_all(
        [
            Faculty(
                nuid=1001,
                first_name="A",
                last_name="X",
                email="a@x.com",
                campus="Boston",
            ),
            Faculty(
                nuid=1002,
                first_name="B",
                last_name="Y",
                email="b@y.com",
                campus="Oakland",
            ),
        ]
    )
    db_session.commit()

    response = client.get("/faculty?campus=Boston")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["FirstName"] == "A"


def test_get_faculty_filter_active_only(client, db_session):
    db_session.add_all(
        [
            Faculty(
                nuid=1001,
                first_name="A",
                last_name="X",
                email="a@x.com",
                campus="Boston",
                active=True,
            ),
            Faculty(
                nuid=1002,
                first_name="B",
                last_name="Y",
                email="b@y.com",
                campus="Boston",
                active=False,
            ),
        ]
    )
    db_session.commit()

    response = client.get("/faculty?active_only=true")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["NUID"] == 1001


def test_get_faculty_profile(client, db_session):
    campus = _make_campus(db_session)
    faculty = Faculty(
        nuid=1001,
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        title="Professor",
        campus=campus.campus_id,
    )
    db_session.add(faculty)
    db_session.commit()

    response = client.get(f"/faculty/{faculty.nuid}")
    assert response.status_code == 200
    data = response.json()
    assert data["nuid"] == 1001
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Doe"
    assert data["email"] == "jane@example.com"
    assert data["title"] == "Professor"
    assert data["campus"] == 1
    assert "course_preferences" in data
    assert "meeting_preferences" in data


def test_get_faculty_profile_with_preferences(client, db_session):
    course = Course(name="Algorithms", description="Algo", credits=4)
    db_session.add(course)
    db_session.flush()
    campus = _make_campus(db_session)
    faculty = Faculty(
        nuid=2001,
        first_name="John",
        last_name="Smith",
        email="john@example.com",
        title="Associate Professor",
        campus=campus.campus_id,
    )
    db_session.add(faculty)
    db_session.flush()

    campus = _make_campus(db_session, name="Boston")
    tb = _make_time_block(db_session, campus_id=campus.campus_id)

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

    response = client.get(f"/faculty/{faculty.nuid}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["course_preferences"]) == 1
    assert data["course_preferences"][0]["course_name"] == "Algorithms"
    assert data["course_preferences"][0]["preference"] == "Eager to teach"
    assert len(data["meeting_preferences"]) == 1
    assert data["meeting_preferences"][0]["preference"] == "Ready to teach"


def test_get_faculty_not_found(client, db_session):
    response = client.get("/faculty/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Faculty not found"


def test_create_faculty_success(client, db_session):
    response = client.post(
        "/faculty",
        json={
            "nuid": 5001,
            "first_name": "Pat",
            "last_name": "Kim",
            "email": "pat.kim@example.edu",
            "campus": "Boston",
            "title": "Lecturer",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["NUID"] == 5001
    assert data["FirstName"] == "Pat"
    assert data["Email"] == "pat.kim@example.edu"
    assert data["Active"] is True


def test_create_faculty_duplicate_nuid_returns_400(client, db_session):
    db_session.add(
        Faculty(
            nuid=6001,
            first_name="A",
            last_name="B",
            email="a@b.edu",
            campus="Boston",
        )
    )
    db_session.commit()

    response = client.post(
        "/faculty",
        json={
            "nuid": 6001,
            "first_name": "C",
            "last_name": "D",
            "email": "other@b.edu",
            "campus": "Boston",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "NUID already exists"


def test_create_faculty_duplicate_email_returns_400(client, db_session):
    db_session.add(
        Faculty(
            nuid=6002,
            first_name="A",
            last_name="B",
            email="shared@b.edu",
            campus="Boston",
        )
    )
    db_session.commit()

    response = client.post(
        "/faculty",
        json={
            "nuid": 6003,
            "first_name": "C",
            "last_name": "D",
            "email": "shared@b.edu",
            "campus": "Boston",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already exists"


def test_patch_faculty_success(client, db_session):
    db_session.add(
        Faculty(
            nuid=7001,
            first_name="Old",
            last_name="Name",
            email="old@example.edu",
            campus="Boston",
            active=True,
        )
    )
    db_session.commit()

    response = client.patch(
        "/faculty/7001",
        json={
            "first_name": "New",
            "active": False,
            "title": "Professor",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["FirstName"] == "New"
    assert data["Active"] is False
    assert data["Title"] == "Professor"


def test_patch_faculty_not_found_returns_404(client, db_session):
    response = client.patch("/faculty/99999", json={"first_name": "X"})
    assert response.status_code == 404


def test_patch_faculty_duplicate_email_returns_400(client, db_session):
    db_session.add_all(
        [
            Faculty(
                nuid=8001,
                first_name="A",
                last_name="One",
                email="a1@example.edu",
                campus="Boston",
            ),
            Faculty(
                nuid=8002,
                first_name="B",
                last_name="Two",
                email="b2@example.edu",
                campus="Boston",
            ),
        ]
    )
    db_session.commit()

    response = client.patch(
        "/faculty/8002",
        json={"email": "a1@example.edu"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already exists"


def test_delete_faculty_success(client, db_session):
    db_session.add(
        Faculty(
            nuid=9001,
            first_name="Gone",
            last_name="Soon",
            email="gone@example.edu",
            campus="Boston",
        )
    )
    db_session.commit()

    response = client.delete("/faculty/9001")
    assert response.status_code == 204
    assert db_session.get(Faculty, 9001) is None


def test_delete_faculty_removes_preferences_and_assignments(client, db_session):
    course = Course(name="PL", description="PL", credits=4)
    campus = _make_campus(db_session, name="Boston")
    tb = _make_time_block(db_session, campus_id=campus.campus_id)
    faculty = Faculty(
        nuid=9002,
        first_name="Rich",
        last_name="Prefs",
        email="prefs@example.edu",
        campus="Boston",
    )
    db_session.add_all([course, tb, faculty])
    db_session.flush()
    semester = _make_semester(db_session, season="Fall", year=2024)
    schedule = Schedule(
        name="F24",
        semester_id=semester.semester_id,
        campus=campus.campus_id,
        draft=True,
    )
    db_session.add(schedule)
    db_session.flush()
    section = Section(
        schedule_id=schedule.schedule_id,
        time_block_id=tb.time_block_id,
        course_id=course.course_id,
        section_number=1,
        capacity=20,
    )
    db_session.add(section)
    db_session.flush()
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
    db_session.add(FacultyAssignment(faculty_nuid=faculty.nuid, section_id=section.section_id))
    db_session.commit()

    assert client.delete(f"/faculty/{faculty.nuid}").status_code == 204
    assert db_session.get(Faculty, faculty.nuid) is None


def test_delete_faculty_not_found_returns_404(client, db_session):
    response = client.delete("/faculty/99999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# build_profile
# ---------------------------------------------------------------------------


def _make_faculty(db, campus_id, nuid=1001):
    faculty = Faculty(
        nuid=nuid,
        first_name="Jane",
        last_name="Doe",
        email=f"faculty{nuid}@example.com",
        campus=campus_id,
    )
    db.add(faculty)
    db.flush()
    return faculty


def _make_course(db, name="Algorithms"):
    course = Course(name=name, description="desc", credits=4)
    db.add(course)
    db.flush()
    return course


def _make_section_with_time_block(db, schedule_id, course_id, time_block_id):
    section = Section(
        schedule_id=schedule_id,
        time_block_id=time_block_id,
        course_id=course_id,
        section_number=1,
        capacity=20,
    )
    db.add(section)
    db.flush()
    return section


class TestBuildProfile:
    def test_returns_existing_preferences_when_present(self, db_session):
        """Faculty with explicit preferences: build_profile returns those preferences."""
        campus = _make_campus(db_session)
        tb = _make_time_block(db_session, campus.campus_id)
        faculty = _make_faculty(db_session, campus.campus_id)
        course = _make_course(db_session)

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

        profile = faculty_service.build_profile(db_session, faculty.nuid)

        assert profile.needsAdminReview is False
        assert len(profile.course_preferences) == 1
        assert profile.course_preferences[0].course_id == course.course_id
        assert profile.course_preferences[0].preference == PreferenceLevel.EAGER
        assert len(profile.meeting_preferences) == 1

    def test_promotes_ready_to_eager_when_no_eager_preferences(self, db_session):
        """Normalization: if no EAGER courses exist, READY courses are promoted to EAGER."""
        campus = _make_campus(db_session)
        _make_time_block(db_session, campus.campus_id)
        faculty = _make_faculty(db_session, campus.campus_id)
        course1 = _make_course(db_session, name="Algorithms")
        course2 = _make_course(db_session, name="OS")

        db_session.add(
            CoursePreference(
                faculty_nuid=faculty.nuid,
                course_id=course1.course_id,
                preference=PreferenceLevel.READY,
            )
        )
        db_session.add(
            CoursePreference(
                faculty_nuid=faculty.nuid,
                course_id=course2.course_id,
                preference=PreferenceLevel.WILLING,
            )
        )
        db_session.commit()

        profile = faculty_service.build_profile(db_session, faculty.nuid)

        eager_ids = {
            cp.course_id
            for cp in profile.course_preferences
            if cp.preference == PreferenceLevel.EAGER
        }
        ready_ids = {
            cp.course_id
            for cp in profile.course_preferences
            if cp.preference == PreferenceLevel.READY
        }
        assert course1.course_id in eager_ids
        assert course2.course_id in ready_ids

    def test_derives_preferences_from_previous_assignments(self, db_session):
        campus = _make_campus(db_session)
        tb = _make_time_block(db_session, campus.campus_id)
        faculty = _make_faculty(db_session, campus.campus_id)
        course = _make_course(db_session)

        sem_prev = _make_semester(db_session, season="Fall", year=2025)

        schedule = Schedule(
            name="F25",
            semester_id=sem_prev.semester_id,
            campus=campus.campus_id,
            draft=False,
        )
        db_session.add(schedule)
        db_session.flush()

        section = _make_section_with_time_block(
            db_session, schedule.schedule_id, course.course_id, tb.time_block_id
        )
        db_session.add(FacultyAssignment(faculty_nuid=faculty.nuid, section_id=section.section_id))
        db_session.commit()

        profile = faculty_service.build_profile(db_session, faculty.nuid)

        assert profile.needsAdminReview is False
        assert len(profile.course_preferences) == 1
        assert profile.course_preferences[0].course_id == course.course_id
        assert profile.course_preferences[0].preference == PreferenceLevel.EAGER
        assert len(profile.meeting_preferences) == 1
        assert profile.meeting_preferences[0].preference == PreferenceLevel.EAGER

    def test_returns_empty_profile_with_needs_admin_review_when_no_data(self, db_session):
        """No preferences and no previous assignments: empty profile flagged for admin review."""
        campus = _make_campus(db_session)
        faculty = _make_faculty(db_session, campus.campus_id)
        db_session.commit()

        profile = faculty_service.build_profile(db_session, faculty.nuid)

        assert profile.needsAdminReview is True
        assert profile.course_preferences == []
        assert profile.meeting_preferences == []


def _make_assignment(section_id):
    a = FacultyAssignment()
    a.section_id = section_id
    return a


def _make_section(section_id, schedule_id):
    s = Section()
    s.section_id = section_id
    s.schedule_id = schedule_id
    return s


def _make_schedule(schedule_id, semester_id):
    sc = Schedule()
    sc.schedule_id = schedule_id
    sc.semester_id = semester_id
    return sc


class TestGetAverageMaxLoad:
    def _run(self, assignments, section_map, schedule_map):
        """Helper: patches repos and calls get_average_max_load."""
        db = MagicMock()

        def mock_get_section(db, section_id):
            return section_map[section_id]

        def mock_get_schedule(db, schedule_id):
            return schedule_map[schedule_id]

        with (
            patch("app.services.faculty.section_repo.get_by_id", side_effect=mock_get_section),
            patch("app.services.faculty.schedule_repo.get_by_id", side_effect=mock_get_schedule),
        ):
            return faculty_service.get_average_max_load(db, assignments)

    def test_equal_load_each_semester(self):
        """2 sections in each of 2 semesters → average 2."""
        assignments = [
            _make_assignment(1),
            _make_assignment(2),  # semester 10
            _make_assignment(3),
            _make_assignment(4),  # semester 11
        ]
        sections = {
            1: _make_section(1, 100),
            2: _make_section(2, 100),
            3: _make_section(3, 101),
            4: _make_section(4, 101),
        }
        schedules = {100: _make_schedule(100, 10), 101: _make_schedule(101, 11)}

        assert self._run(assignments, sections, schedules) == 2

    def test_unequal_load_rounds_correctly(self):
        """3 sections in semester 1, 2 in semester 2 → average 2.5 → rounds to 3."""
        assignments = [
            _make_assignment(1),
            _make_assignment(2),
            _make_assignment(3),  # semester 10
            _make_assignment(4),
            _make_assignment(5),  # semester 11
        ]
        sections = {
            1: _make_section(1, 100),
            2: _make_section(2, 100),
            3: _make_section(3, 100),
            4: _make_section(4, 101),
            5: _make_section(5, 101),
        }
        schedules = {100: _make_schedule(100, 10), 101: _make_schedule(101, 11)}

        assert self._run(assignments, sections, schedules) == 3

    def test_single_semester(self):
        """All sections in one semester → average equals that count."""
        assignments = [_make_assignment(1), _make_assignment(2), _make_assignment(3)]
        sections = {i: _make_section(i, 100) for i in [1, 2, 3]}
        schedules = {100: _make_schedule(100, 10)}

        assert self._run(assignments, sections, schedules) == 3

    def test_one_section_per_semester(self):
        """1 section across 3 semesters → average 1."""
        assignments = [_make_assignment(1), _make_assignment(2), _make_assignment(3)]
        sections = {1: _make_section(1, 100), 2: _make_section(2, 101), 3: _make_section(3, 102)}
        schedules = {
            100: _make_schedule(100, 10),
            101: _make_schedule(101, 11),
            102: _make_schedule(102, 12),
        }

        assert self._run(assignments, sections, schedules) == 1
