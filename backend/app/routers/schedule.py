"""Schedule router."""

import csv
from collections import defaultdict
from io import StringIO

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.campus import Campus
from app.models.time_block import TimeBlock
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
    """Export a finalized schedule as a downloadable CSV."""
    schedule = schedule_service.get_by_id(db, schedule_id)
    if schedule.draft:
        raise HTTPException(status_code=400, detail="Schedule must be finalized before exporting")

    campus_obj = db.query(Campus).filter(Campus.campus_id == schedule.campus).first()
    campus_name = campus_obj.name if campus_obj else str(schedule.campus)

    all_tbs = db.query(TimeBlock).filter(TimeBlock.campus == schedule.campus).all()
    tb_by_id = {tb.time_block_id: tb for tb in all_tbs}
    tb_by_group: dict[str, list] = defaultdict(list)
    for tb in all_tbs:
        if tb.block_group:
            tb_by_group[tb.block_group].append(tb)
    for blocks in tb_by_group.values():
        blocks.sort(key=lambda tb: tb.start_time)

    def _fmt(t) -> str:
        return t.strftime("%I:%M %p").lstrip("0")

    def _safe(v: object) -> str:
        s = "" if v is None else str(v)
        return "'" + s if s and s[0] in ("=", "+", "-", "@", "\t", "\r") else s

    sections = section_service.get_rich_sections(db, schedule_id)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "course_name",
            "section_number",
            "instructor_name",
            "instructor_nuid",
            "time_block",
            "room",
            "capacity",
            "campus",
            "cross_listed_with",
            "course_pref_level",
            "time_pref_level",
        ]
    )

    for section in sections:
        raw_tb = tb_by_id.get(section.time_block.time_block_id)
        if raw_tb and raw_tb.block_group:
            siblings = tb_by_group.get(raw_tb.block_group, [raw_tb])
            time_block = " / ".join(
                f"{p.meeting_days} {_fmt(p.start_time)}-{_fmt(p.end_time)}" for p in siblings
            )
        else:
            time_block = (
                f"{section.time_block.days} "
                f"{section.time_block.start_time}-{section.time_block.end_time}"
            )

        instructors = sorted(section.instructors, key=lambda i: (i.last_name, i.nuid))
        if instructors:
            instructor_name = "; ".join(f"{i.first_name} {i.last_name}" for i in instructors)
            instructor_nuid = "; ".join(i.nuid for i in instructors)
            course_pref = "; ".join(
                next(
                    (cp.preference for cp in i.course_preferences if cp.course_id == section.course.course_id),
                    "",
                )
                for i in instructors
            )
            time_pref = "; ".join(
                next(
                    (mp.preference for mp in i.meeting_preferences if mp.time_block_id == section.time_block.time_block_id),
                    "",
                )
                for i in instructors
            )
        else:
            instructor_name = ""
            instructor_nuid = ""
            course_pref = ""
            time_pref = ""

        writer.writerow(
            [
                _safe(section.course.name),
                section.section_number,
                _safe(instructor_name),
                instructor_nuid,
                time_block,
                _safe(section.room or ""),
                section.capacity,
                campus_name,
                section.crosslisted_section_id or "",
                _safe(course_pref),
                _safe(time_pref),
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="schedule_{schedule_id}.csv"'},
    )


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
