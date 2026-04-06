"""Section lock router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.section_lock import SectionLockResponse
from app.services import section_lock as section_lock_service
from app.services.section_lock import SectionLockConflictError

router = APIRouter(prefix="/sections", tags=["section_locks"])


@router.post("/{section_id}/lock", response_model=SectionLockResponse)
def acquire_lock(
    section_id: int,
    # TODO: replace user_id with current user from auth once SSIP-61/62 is ready
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Acquire a lock on a section for editing.

    Args:
        section_id: ID of the section to lock.
        user_id: ID of the user acquiring the lock.
        db: Database session.

    Raises:
        HTTPException: 403 if the user does not have the ADMIN role.
        HTTPException: 423 if the section is locked by another user.
    """
    db_user = db.query(User).filter(User.nuid == user_id).first()

    if not db_user or db_user.role != "ADMIN":
        raise HTTPException(
            status_code=403, detail="Only ADMIN role users may acquire locks"
        )

    try:
        return section_lock_service.acquire_lock(db, section_id, user_id)
    except SectionLockConflictError as e:
        raise HTTPException(
            status_code=423,
            detail={
                "locked_by": e.lock.locked_by,
                "expires_at": str(e.lock.expires_at),
            },
        ) from e


@router.post("/{section_id}/unlock")
def release_lock(
    section_id: int,
    # TODO: replace user_id with current user from auth once SSIP-61/62 is ready
    user_id: int,
    db: Session = Depends(get_db),
):
    """Release a lock on a section.

    Args:
        section_id: ID of the section to unlock.
        user_id: ID of the user releasing the lock.
        db: Database session.

    Raises:
        HTTPException: 403 if the caller does not own an active lock.
    """
    try:
        section_lock_service.release_lock(db, section_id, user_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
