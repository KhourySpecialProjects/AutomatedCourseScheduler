"""Schedule Warning router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.database import get_db
from app.core.enums import Severity, WarningType
from app.models.schedule_warning import ScheduleWarning as ScheduleWarningModel
from app.models.user import User
from app.repositories import schedule as schedule_repo
from app.repositories import schedule_warning as warning_repo
from app.schemas.warning import Warning, WarningResponse
from app.services.connection_manager import manager

router = APIRouter(prefix="/schedules", tags=["warnings"])


def _to_response(r: ScheduleWarningModel) -> WarningResponse:
    return WarningResponse(
        warning_id=r.warning_id,
        section_id=r.section_id,
        Type=r.type if r.type in WarningType._value2member_map_ else None,
        SeverityRank=int(r.severity) if r.severity.isdigit() else Severity.MEDIUM,
        Message=r.message,
        FacultyID=r.faculty_nuid,
        CourseID=r.course_id,
        BlockID=r.time_block_id,
        dismissed=r.dismissed,
        dismissed_by=r.dismissed_by,
    )


@router.get("/{schedule_id}/warnings", response_model=list[WarningResponse])
def get_schedule_warnings(
    schedule_id: int,
    type: str | None = None,
    severity: str | None = None,
    include_dismissed: bool = Query(False),
    db: Session = Depends(get_db),
):
    if not schedule_repo.schedule_exists(db, schedule_id):
        raise HTTPException(status_code=404, detail="Schedule not found")

    rows = warning_repo.get_by_schedule(
        db,
        schedule_id,
        warning_type=type,
        severity=severity,
        include_dismissed=include_dismissed,
    )
    return [_to_response(r) for r in rows]


@router.post("/{schedule_id}/warnings", response_model=WarningResponse, status_code=201)
def create_warning(
    schedule_id: int,
    warning: Warning,
    db: Session = Depends(get_db),
):
    if not schedule_repo.schedule_exists(db, schedule_id):
        raise HTTPException(status_code=404, detail="Schedule not found")

    row = ScheduleWarningModel(
        schedule_id=schedule_id,
        type=warning.Type.value if warning.Type else "manual",
        severity=str(warning.SeverityRank.value),
        message=warning.Message,
        faculty_nuid=warning.FacultyID,
        course_id=warning.CourseID,
        time_block_id=warning.BlockID,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return _to_response(row)


@router.patch("/{schedule_id}/warnings/{warning_id}/dismiss")
async def dismiss_warning(
    schedule_id: int,
    warning_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if not schedule_repo.schedule_exists(db, schedule_id):
        raise HTTPException(status_code=404, detail="Schedule not found")

    warning = warning_repo.get_by_id(db, warning_id)
    if warning is None or warning.schedule_id != schedule_id:
        raise HTTPException(status_code=404, detail="Warning not found")

    warning.dismissed = True
    warning.dismissed_by = f"{current_user.first_name} {current_user.last_name}"
    db.commit()

    await manager.broadcast(
        schedule_id,
        {
            "type": "section_warnings",
            "payload": {"section_id": warning.section_id, "warnings": []},
        },
    )
    return {"warning_id": warning_id, "dismissed": True}


@router.patch("/{schedule_id}/warnings/{warning_id}/restore")
async def restore_warning(
    schedule_id: int,
    warning_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if not schedule_repo.schedule_exists(db, schedule_id):
        raise HTTPException(status_code=404, detail="Schedule not found")

    warning = warning_repo.get_by_id(db, warning_id)
    if warning is None or warning.schedule_id != schedule_id:
        raise HTTPException(status_code=404, detail="Warning not found")

    warning.dismissed = False
    warning.dismissed_by = None
    db.commit()

    await manager.broadcast(
        schedule_id,
        {
            "type": "section_warnings",
            "payload": {"section_id": warning.section_id, "warnings": []},
        },
    )
    return {"warning_id": warning_id, "dismissed": False}


@router.delete("/{schedule_id}/warnings/{warning_id}", status_code=204)
async def delete_warning(
    schedule_id: int,
    warning_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if not schedule_repo.schedule_exists(db, schedule_id):
        raise HTTPException(status_code=404, detail="Schedule not found")

    warning = warning_repo.get_by_id(db, warning_id)
    if warning is None or warning.schedule_id != schedule_id:
        raise HTTPException(status_code=404, detail="Warning not found")

    section_id = warning.section_id
    db.delete(warning)
    db.commit()

    await manager.broadcast(
        schedule_id,
        {
            "type": "section_warnings",
            "payload": {"section_id": section_id, "warnings": []},
        },
    )
