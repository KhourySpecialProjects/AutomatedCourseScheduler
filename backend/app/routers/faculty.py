"""Faculty router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.course_preference import CoursePreference
from app.models.faculty import Faculty
from app.schemas.faculty import FacultyProfileResponse, FacultyResponse
from app.schemas.section import CoursePreferenceInfo, MeetingPreferenceInfo

router = APIRouter(prefix="/faculty", tags=["faculty"])


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


@router.get("", response_model=list[FacultyResponse])
def get_faculty(
    campus: str | None = Query(None, description="Filter by campus name"),
    active_only: bool = Query(False, description="Filter to only active faculty"),
    db: Session = Depends(get_db),
):
    """Retrieve all faculty members."""
    query = db.query(Faculty)
    if campus is not None:
        query = query.filter(Faculty.campus == campus)
    if active_only:
        query = query.filter(Faculty.active.is_(True))
    faculty_list = query.order_by(Faculty.last_name, Faculty.first_name).all()
    return [_faculty_to_response(f) for f in faculty_list]


@router.get("/{nuid}", response_model=FacultyProfileResponse)
def get_faculty_profile(nuid: int, db: Session = Depends(get_db)):
    "Retrieve faculty profile with course and time preferences."
    faculty = (
        db.query(Faculty)
        .options(
            joinedload(Faculty.course_preferences).joinedload(CoursePreference.course),
            joinedload(Faculty.meeting_preferences),
        )
        .filter(Faculty.nuid == nuid)
        .first()
    )
    if faculty is None:
        raise HTTPException(status_code=404, detail="Faculty not found")
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
