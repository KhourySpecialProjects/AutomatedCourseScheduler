"""Schedule service — business logic."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.schedule import Schedule
from app.models.section import Section
from app.repositories import schedule as schedule_repo
from app.schemas.course import CourseResponse
from app.schemas.schedule import ScheduleCreate, ScheduleResponse, ScheduleUpdate

STUB_SECTION_CAPACITY = 30


def get_all(db, campus_id=None, semester_id=None):
    return schedule_repo.get_all(db, campus_id=campus_id, semester_id=semester_id)


def get_by_id(db: Session, schedule_id: int):
    schedule = schedule_repo.get_by_id(db, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


def create(db: Session, data: ScheduleCreate) -> Schedule:
    to_create = {
        "name": data.name,
        "semester_id": data.semester_id,
        "campus": data.campus,
    }
    return schedule_repo.create(db, to_create)


def update(db: Session, schedule_id: int, data: ScheduleUpdate):
    updated = schedule_repo.update(db, schedule_id, data.model_dump(exclude_unset=True))
    if updated is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return updated


def delete(db: Session, schedule_id: int) -> None:
    success = schedule_repo.delete(db, schedule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Schedule not found")


def add_course_list(
    db: Session, schedule: Schedule, course_list: list[CourseResponse]
) -> ScheduleResponse:
    # Persist stub sections so the algorithm can discover which courses belong
    # to this schedule (via section.schedule_id) and how many sections each
    # needs. The algorithm fills in time_block_id / faculty_assignments later.
    for course in course_list:
        for n in range(1, (course.section_count or 0) + 1):
            db.add(
                Section(
                    schedule_id=schedule.schedule_id,
                    course_id=course.course_id,
                    section_number=n,
                    capacity=STUB_SECTION_CAPACITY,
                    time_block_id=None,
                )
            )
    db.commit()

    return ScheduleResponse(
        schedule_id=schedule.schedule_id,
        name=schedule.name,
        semester_id=schedule.semester_id,
        draft=schedule.draft,
        campus=schedule.campus,
        active=schedule.active,
        status=schedule.status,
        error_message=schedule.error_message,
        course_list=course_list,
    )
