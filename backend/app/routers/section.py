"""Section router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.section import (
    SectionCreate,
    SectionResponse,
    SectionRichResponse,
    SectionUpdate,
)
from app.services import section as section_service
from app.services import section_lock as section_lock_service
from app.services.connection_manager import manager
from app.services.section_lock import SectionLockConflictError

router = APIRouter(prefix="/sections", tags=["sections"])


@router.post("", response_model=SectionResponse, status_code=201)
async def create_section(section: SectionCreate, db: Session = Depends(get_db)):
    """Create a new section in a schedule."""
    try:
        created = section_service.create_section(db, section)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    rich_sections = section_service.get_rich_sections(db, created.schedule_id)
    rich_section = next((s for s in rich_sections if s.section_id == created.section_id), None)
    if rich_section:
        await manager.broadcast(
            created.schedule_id,
            {
                "type": "section_created",
                "payload": SectionRichResponse.model_validate(rich_section).model_dump(mode="json"),
            },
        )

    return created


@router.patch("/{section_id}", response_model=SectionResponse)
async def update_section(
    section_id: int,
    section: SectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Acquire (or refresh) the lock on this section, then apply the update.

    Fails with 423 if another user currently holds the lock.
    Broadcasts section_updated to connected clients on success.
    """
    display_name = f"{current_user.first_name} {current_user.last_name}"
    try:
        await section_lock_service.acquire_lock(db, section_id, current_user.user_id, display_name)
    except SectionLockConflictError as e:
        raise HTTPException(
            status_code=423,
            detail={"locked_by": e.lock.locked_by, "expires_at": str(e.lock.expires_at)},
        ) from e
    try:
        result = section_service.update_section(db, section_id, section)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if result is None:
        raise HTTPException(status_code=404, detail="Section not found")

    updated = result["updated"]
    warnings = result["warnings"]
    partner_ids: list[int] = result.get("partner_ids", [])

    rich_sections = section_service.get_rich_sections(db, updated.schedule_id)

    for sid in [section_id, *partner_ids]:
        rich = next((s for s in rich_sections if s.section_id == sid), None)
        if rich:
            await manager.broadcast(
                updated.schedule_id,
                {
                    "type": "section_updated",
                    "payload": {"section_id": sid, "data": rich.model_dump(mode="json")},
                },
            )

    if warnings:
        await manager.broadcast(
            updated.schedule_id,
            {
                "type": "section_warnings",
                "payload": {
                    "section_id": section_id,
                    "warnings": [w.value for w in warnings],
                },
            },
        )

    return updated


@router.delete("/{section_id}", status_code=204)
async def delete_section(section_id: int, db: Session = Depends(get_db)):
    """Delete a section from a schedule."""
    section = section_service.get_by_id(db, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    ok, partner_ids_to_broadcast = section_service.delete_section(db, section_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Section not found")

    await manager.broadcast(
        section.schedule_id,
        {"type": "section_deleted", "payload": {"section_id": section_id}},
    )

    if partner_ids_to_broadcast:
        rich_sections = section_service.get_rich_sections(db, section.schedule_id)

        async def _broadcast_section_updated(sid: int) -> None:
            rich = next((s for s in rich_sections if s.section_id == sid), None)
            if rich:
                await manager.broadcast(
                    section.schedule_id,
                    {
                        "type": "section_updated",
                        "payload": {
                            "section_id": sid,
                            "data": rich.model_dump(mode="json"),
                        },
                    },
                )

        for pid in partner_ids_to_broadcast:
            await _broadcast_section_updated(pid)
