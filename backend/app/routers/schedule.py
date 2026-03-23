"""Schedule router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.enums import Semester
from app.models.schedule import Schedule
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleResponse,
    ScheduleUpdate,
)
from app.schemas.section import SectionRichResponse
from app.services import section as section_service

router = APIRouter(prefix="/schedules", tags=["schedules"])


def _schedule_to_response(schedule: Schedule) -> ScheduleResponse:
    """Build ScheduleResponse from Schedule ORM."""
    return ScheduleResponse(
        ScheduleID=schedule.schedule_id,
        ScheduleName=schedule.name,
        SemesterSeason=schedule.semester.value,
        SemesterYear=schedule.year,
        Campus=None,
        Complete=not schedule.draft,
    )


def _parse_semester(value: str) -> Semester | None:
    """Parse string to Semester enum by value (e.g. 'Fall' -> Semester.FALL)."""
    for s in Semester:
        if s.value == value:
            return s
    return None


@router.get("", response_model=list[ScheduleResponse])
def get_schedules(
    campus_id: int | None = Query(None, description="Filter by campus ID"),
    semester_season: str | None = Query(
        None, description="Filter by semester season (e.g. Fall, Spring)"
    ),
    semester_year: int | None = Query(None, description="Filter by semester year"),
    db: Session = Depends(get_db),
):
    """Retrieve all schedules, optionally filtered by semester."""
    query = db.query(Schedule)
    if semester_season is not None:
        sem = _parse_semester(semester_season)
        if sem is None:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid semester_season: {[s.value for s in Semester]}",
            )
        query = query.filter(Schedule.semester == sem)
    if semester_year is not None:
        query = query.filter(Schedule.year == semester_year)
    schedules = query.order_by(Schedule.year.desc(), Schedule.name).all()
    return [_schedule_to_response(s) for s in schedules]


@router.post("", response_model=ScheduleResponse, status_code=201)
def create_schedule(schedule: ScheduleCreate, db: Session = Depends(get_db)):
    """Create a new schedule draft."""
    # TODO: Implement schedule creation
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific schedule (name, semester, year, campus, status)."""
    schedule = db.query(Schedule).filter(Schedule.schedule_id == schedule_id).first()
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return _schedule_to_response(schedule)


@router.get("/{schedule_id}/sections", response_model=list[SectionRichResponse])
def get_schedule_sections(schedule_id: int, db: Session = Depends(get_db)):
    """Get all sections for a specific schedule with nested course and faculty data."""
    schedule = db.query(Schedule).filter(Schedule.schedule_id == schedule_id).first()
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return section_service.get_rich_sections(db, schedule_id)


@router.put("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: int, schedule: ScheduleUpdate, db: Session = Depends(get_db)
):
    """Update schedule metadata (name, complete status, etc.)."""
    # TODO: Implement schedule update
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/{schedule_id}", status_code=204)
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """Delete a schedule and all its sections."""
    # TODO: Implement schedule deletion
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/{schedule_id}/generate", response_model=ScheduleResponse)
def generate_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """Trigger the scheduling algorithm to generate a draft schedule."""
    # TODO: Implement schedule generation algorithm
    raise HTTPException(status_code=501, detail="Algorithm not yet implemented")


@router.get("/{schedule_id}/export/csv")
def export_schedule_csv(schedule_id: int, db: Session = Depends(get_db)):
    """Export a finalized schedule in CourseLeaf-compatible CSV format."""
    # TODO: Implement CSV export
    raise HTTPException(status_code=501, detail="Not implemented yet")
