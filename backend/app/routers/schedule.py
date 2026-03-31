"""Schedule router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleResponse,
    ScheduleUpdate,
)
from app.schemas.section import SectionResponse, SectionRichResponse
from app.services import schedule as schedule_service
from app.services import section as section_service
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
    return schedule_service.create(db, schedule)


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
def update_schedule(
    schedule_id: int, schedule: ScheduleUpdate, db: Session = Depends(get_db)
):
    """Update schedule metadata (name, complete status, etc.)."""
    return schedule_service.update(db, schedule_id, schedule)


@router.delete("/{schedule_id}", status_code=204)
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """Delete a schedule and all its sections."""
    schedule_service.delete(db, schedule_id)


@router.get("/{schedule_id}/export/csv")
def export_schedule_csv(schedule_id: int, db: Session = Depends(get_db)):
    """Export a finalized schedule in CourseLeaf-compatible CSV format."""
    # TODO: Implement CSV export
    raise HTTPException(status_code=501, detail="Not implemented yet")
