"""Section lock router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
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
    """Acquire a lock on a section for editing."""
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
