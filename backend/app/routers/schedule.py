"""Schedule router."""

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleResponse,
    ScheduleUpdate,
)
from app.schemas.section import SectionResponse, SectionRichResponse
from app.schemas.section_lock import ScheduleActiveLockResponse
from app.services import course as course_service
from app.services import schedule as schedule_service
from app.services import section as section_service
from app.services import section_lock as section_lock_service
from app.services import semester as semester_service
from app.services.connection_manager import manager
from app.services.section import ScheduleNotFoundError

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("", response_model=list[ScheduleResponse])
def get_schedules(
    campus_id: int | None = Query(None),
    semester_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    return schedule_service.get_all(db, campus_id=campus_id, semester_id=semester_id)


@router.post("", response_model=ScheduleResponse, status_code=201)
def create_schedule(schedule: ScheduleCreate, db: Session = Depends(get_db)):
    """Create a new schedule draft."""

    created = schedule_service.create(db, schedule)
    previous_year = semester_service.get_last_year(db, created.semester_id)
    if previous_year is None:
        course_list = []
    else:
        try:
            course_list = course_service.generate_course_list(
                db, previous_year, schedule.new_courses, schedule.campus
            )
        except ValueError as e:
            course_list = []
            raise HTTPException(status_code=404, detail=e.args[0]) from e

    return schedule_service.add_course_list(db, created, course_list)


@router.get("/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific schedule."""
    return schedule_service.get_by_id(db, schedule_id)


@router.get("/{schedule_id}/sections", response_model=list[SectionResponse])
def get_schedule_sections(schedule_id: int, db: Session = Depends(get_db)):
    """Get all sections for a specific schedule."""
    try:
        section_service.require_schedule(db, schedule_id)
        return section_service.get_all_sections(db, schedule_id)
    except ScheduleNotFoundError:
        raise HTTPException(status_code=404, detail="Schedule not found") from None


@router.get("/{schedule_id}/sections/rich", response_model=list[SectionRichResponse])
def get_schedule_sections_rich(schedule_id: int, db: Session = Depends(get_db)):
    """Get all sections with denormalized course, time block, and instructor data."""
    try:
        section_service.require_schedule(db, schedule_id)
        return section_service.get_rich_sections(db, schedule_id)
    except ScheduleNotFoundError:
        raise HTTPException(status_code=404, detail="Schedule not found") from None


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule: ScheduleUpdate = Body(default=None),
    db: Session = Depends(get_db),
):
    """Update schedule metadata (name, complete status, etc.)."""
    updated = schedule_service.update(db, schedule_id, schedule or ScheduleUpdate())
    await manager.broadcast(
        schedule_id,
        {
            "type": "schedule_updated",
            "payload": ScheduleResponse.model_validate(updated).model_dump(mode="json"),
        },
    )
    return updated


@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """Delete a schedule and all its sections."""
    schedule_service.delete(db, schedule_id)
    await manager.broadcast(
        schedule_id,
        {"type": "schedule_deleted", "payload": {"schedule_id": schedule_id}},
    )
    await manager.disconnect_all(schedule_id)


@router.get("/{schedule_id}/export/csv")
def export_schedule_csv(schedule_id: int, db: Session = Depends(get_db)):
    """Export a finalized schedule in CourseLeaf-compatible CSV format."""
    # TODO: Implement CSV export
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{schedule_id}/locks", response_model=list[ScheduleActiveLockResponse])
def get_schedule_locks(
    schedule_id: int, db: Session = Depends(get_db)
) -> list[ScheduleActiveLockResponse]:
    """
    Get all active locks for a schedule.

    Args:
        schedule_id: ID of the schedule to query locks for.
        db: Database session.

    Returns:
        List of active locks with user display name included.
    """
    return section_lock_service.get_active_locks_for_schedule(db, schedule_id)
