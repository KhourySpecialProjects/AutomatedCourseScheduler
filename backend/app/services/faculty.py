from sqlalchemy.orm import Session

from app.models.faculty import Faculty
from app.repositories import faculty as faculty_repo
from app.schemas.faculty import (
    FacultyCreate,
    FacultyProfileResponse,
    FacultyResponse,
    FacultyUpdate,
)
from app.schemas.section import CoursePreferenceInfo, MeetingPreferenceInfo


def _faculty_to_response(faculty: Faculty) -> FacultyResponse:
    return FacultyResponse(
        NUID=faculty.nuid,
        FirstName=faculty.first_name,
        LastName=faculty.last_name,
        Email=faculty.email,
        Title=faculty.title,
        Campus=None,
        Active=faculty.active,
        MaxLoad=None,
    )


def get_faculty(
    db: Session, campus: str | None = None, active_only: bool = False
) -> list[FacultyResponse]:
    faculty_list = faculty_repo.get_all(db, campus=campus, active_only=active_only)
    return [_faculty_to_response(f) for f in faculty_list]


def create_faculty(db: Session, body: FacultyCreate) -> FacultyResponse:
    if faculty_repo.get_by_nuid(db, body.nuid) is not None:
        raise ValueError("NUID already exists")
    if faculty_repo.email_in_use_by_other(db, body.email, None):
        raise ValueError("Email already exists")
    faculty = Faculty(
        nuid=body.nuid,
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        campus=body.campus,
        phone_number=body.phone_number,
        title=body.title,
        active=body.active,
    )
    faculty_repo.create(db, faculty)
    return _faculty_to_response(faculty)


def update_faculty(
    db: Session, nuid: int, body: FacultyUpdate
) -> FacultyResponse | None:
    faculty = faculty_repo.get_by_nuid(db, nuid)
    if faculty is None:
        return None
    fields = body.model_fields_set
    if "first_name" in fields:
        if not body.first_name:
            raise ValueError("FirstName is invalid")
        faculty.first_name = body.first_name
    if "last_name" in fields:
        if not body.last_name:
            raise ValueError("LastName is invalid")
        faculty.last_name = body.last_name
    if "email" in fields:
        if not body.email:
            raise ValueError("Email is invalid")
        if faculty_repo.email_in_use_by_other(db, body.email, nuid):
            raise ValueError("Email already exists")
        faculty.email = body.email
    if "campus" in fields:
        if not body.campus:
            raise ValueError("Campus is invalid")
        faculty.campus = body.campus
    if "phone_number" in fields:
        faculty.phone_number = body.phone_number
    if "title" in fields:
        faculty.title = body.title
    if "active" in fields:
        if body.active is None:
            raise ValueError("Active is invalid")
        faculty.active = body.active
    faculty_repo.save(db, faculty)
    return _faculty_to_response(faculty)


def delete_faculty(db: Session, nuid: int) -> bool:
    faculty = faculty_repo.get_by_nuid(db, nuid)
    if faculty is None:
        return False
    faculty_repo.delete_with_dependencies(db, faculty)
    return True


def get_faculty_profile(db: Session, nuid: int) -> FacultyProfileResponse | None:
    faculty = faculty_repo.get_by_nuid_with_preferences(db, nuid)
    if faculty is None:
        return None
    return FacultyProfileResponse(
        nuid=faculty.nuid,
        first_name=faculty.first_name,
        last_name=faculty.last_name,
        email=faculty.email,
        title=faculty.title,
        campus=faculty.campus,
        active=faculty.active,
        course_preferences=[
            CoursePreferenceInfo(
                course_id=cp.course_id,
                course_name=cp.course.name,
                preference=cp.preference.value,
            )
            for cp in faculty.course_preferences
        ],
        meeting_preferences=[
            MeetingPreferenceInfo(
                meeting_time=str(mp.meeting_time),
                preference=mp.preference.value,
            )
            for mp in faculty.meeting_preferences
        ],
    )
