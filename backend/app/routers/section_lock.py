"""Section lock router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.section_lock import SectionLockResponse
from app.services import section_lock as section_lock_service
from app.services.section_lock import SectionLockConflictError

router = APIRouter(prefix="/sections", tags=["section_locks"])


@router.post("/{section_id}/lock", response_model=SectionLockResponse)
async def acquire_lock(
    section_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Acquire a lock on a section for editing.

    Raises:
        HTTPException: 403 if the caller does not have the admin role.
        HTTPException: 423 if the section is locked by another user.
    """
    display_name = f"{current_user.first_name} {current_user.last_name}"
    try:
        return await section_lock_service.acquire_lock(
            db, section_id, current_user.user_id, display_name
        )
    except SectionLockConflictError as e:
        raise HTTPException(
            status_code=423,
            detail={
                "locked_by": e.lock.locked_by,
                "expires_at": str(e.lock.expires_at),
            },
        ) from e


@router.post("/{section_id}/unlock")
async def release_lock(
    section_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Release a lock on a section.

    Raises:
        HTTPException: 403 if the caller does not own an active lock.
    """
    try:
        await section_lock_service.release_lock(db, section_id, current_user.user_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
