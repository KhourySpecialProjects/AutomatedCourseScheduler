from sqlalchemy.orm import Session

from app.models.faculty import Faculty
from app.repositories import faculty as faculty_repo
from app.schemas.faculty import FacultyProfileResponse, FacultyResponse
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
