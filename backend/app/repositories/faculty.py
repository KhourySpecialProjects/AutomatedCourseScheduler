from sqlalchemy.orm import Session, selectinload

from app.models.campus import Campus
from app.core.enums import PreferenceLevel
from app.models.course_preference import CoursePreference
from app.models.meeting_preference import MeetingPreference
from app.models.faculty_assignment import FacultyAssignment
from app.models.faculty import Faculty


def get_all(db: Session, campus: int | None = None, active_only: bool = False) -> list[Faculty]:
    query = db.query(Faculty)
    if campus is not None:
        query = query.join(Campus, Faculty.campus ==
                           Campus.campus_id).filter(Campus.name == campus)
    if active_only:
        query = query.filter(Faculty.active.is_(True))
    return query.order_by(Faculty.last_name, Faculty.first_name).all()


def get_by_nuid(db: Session, nuid: int) -> Faculty | None:
    return db.query(Faculty).filter(Faculty.nuid == nuid).first()


def email_in_use_by_other(db: Session, email: str, exclude_nuid: int | None) -> bool:
    q = db.query(Faculty).filter(Faculty.email == email)
    if exclude_nuid is not None:
        q = q.filter(Faculty.nuid != exclude_nuid)
    return q.first() is not None


def get_by_nuid_with_preferences(db: Session, nuid: int) -> Faculty | None:
    return (
        db.query(Faculty)
        .options(
            selectinload(Faculty.course_preferences).joinedload(
                CoursePreference.course),
            selectinload(Faculty.meeting_preferences),
        )
        .filter(Faculty.nuid == nuid)
        .first()
    )


def faculty_exists(db: Session, faculty_nuid: int) -> bool:
    return db.query(Faculty.nuid).filter(Faculty.nuid == faculty_nuid).first() is not None


def create(db: Session, faculty: Faculty) -> Faculty:
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


def save(db: Session, faculty: Faculty) -> Faculty:
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


def delete_with_dependencies(db: Session, faculty: Faculty) -> None:
    db.delete(faculty)
    db.commit()


def get_assginments(db: Session, faculty_nuid: int) -> list[FacultyAssignment]:
    assignments = db.query(FacultyAssignment).filter(
        FacultyAssignment.faculty_nuid == faculty_nuid).all()

    return assignments


def find_meeting_time_preference(db: Session, nuid: int, time_block_id: int) -> bool:
    pref = (
        db.query(MeetingPreference)
        .filter(
            MeetingPreference.faculty_nuid == nuid,
            MeetingPreference.meeting_time == time_block_id,
        )
        .first()
    )
    if not pref or pref.preference == PreferenceLevel.NOT_INTERESTED:
        return False
    return True


def find_course_preference(db: Session, nuid: int, course_id: int) -> bool:
    pref = (
        db.query(CoursePreference)
        .filter(
            CoursePreference.faculty_nuid == nuid,
            CoursePreference.course_id == course_id,
        )
        .first()
    )
    if not pref or pref.preference == PreferenceLevel.NOT_INTERESTED:
        return False
    return True
