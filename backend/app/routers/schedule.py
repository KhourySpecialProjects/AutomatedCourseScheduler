"""Schedule router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleResponse,
    ScheduleUpdate,
)
from app.schemas.section import SectionResponse
from app.services import section as section_service
from app.services import schedule as schedule_service

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("", response_model=list[ScheduleResponse])
def get_schedules(
    campus_id: int | None = Query(None, description="Filter by campus ID"),
    semester_season: str | None = Query(None, description="Filter by semester season"),
    semester_year: int | None = Query(None, description="Filter by semester year"),
    db: Session = Depends(get_db),
):
    """Retrieve all schedules, optionally filtered by campus or semester."""
    return schedule_service.get_all(db)


@router.post("", response_model=ScheduleResponse, status_code=201)
def create_schedule(schedule: ScheduleCreate, db: Session = Depends(get_db)):
    """Create a new schedule draft."""
    # TODO: Implement schedule creation
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific schedule."""
    return schedule_service.get_by_id(db, schedule_id)


@router.get("/{schedule_id}/sections", response_model=list[SectionResponse])
def get_schedule_sections(schedule_id: int, db: Session = Depends(get_db)):
    """Get all sections for a specific schedule."""
    return section_service.get_all_sections(db, schedule_id=schedule_id)


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
