"""Section lock service — business logic."""

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.section_lock import SectionLock
from app.models.user import User
from app.repositories import section as section_repo
from app.repositories import section_lock as section_lock_repo
from app.schemas.section_lock import ScheduleActiveLockResponse
from app.services.connection_manager import manager


class SectionLockConflictError(Exception):
    """Raised when a section is locked by another user."""

    def __init__(self, lock: SectionLock):
        self.lock = lock


async def acquire_lock(
    db: Session, section_id: int, user_id: int, display_name: str
) -> SectionLock:
    """Acquire a lock on a section for editing, auto-releasing any other lock the user
    currently holds. Broadcasts lock_acquired only when a new lock is created (not on
    refresh of an existing lock by the same user).

    Args:
        db: Database connection.
        section_id: ID of the section to lock.
        user_id: ID of the user acquiring the lock.
        display_name: Full name of the user, included in the broadcast payload.

    Returns:
        The acquired or refreshed SectionLock.

    Raises:
        SectionLockConflictError: If the section is locked by another user.
    """
    now = datetime.now(UTC).replace(tzinfo=None)
    existing_lock = section_lock_repo.get_by_section_id(db, section_id)

    # Lock exists and is active — same user just refreshes the TTL, no broadcast needed.
    if existing_lock and existing_lock.expires_at > now:
        if existing_lock.locked_by == user_id:
            existing_lock.expires_at = now + timedelta(minutes=settings.LOCK_TIMEOUT_MINUTES)
            return section_lock_repo.save(db, existing_lock)
        raise SectionLockConflictError(existing_lock)

    # Auto-release any other lock this user holds on a different section.
    user_existing_lock = section_lock_repo.get_by_user_id(db, user_id)
    if user_existing_lock:
        prev_section = section_repo.get_by_id(db, user_existing_lock.section_id)
        section_lock_repo.delete(db, user_existing_lock)
        if prev_section:
            await manager.broadcast(
                prev_section.schedule_id,
                {"type": "lock_released", "payload": {"section_id": user_existing_lock.section_id}},
            )

    # Delete expired lock on this section if one exists.
    if existing_lock:
        section_lock_repo.delete(db, existing_lock)

    new_lock = SectionLock(
        section_id=section_id,
        locked_by=user_id,
        expires_at=now + timedelta(minutes=settings.LOCK_TIMEOUT_MINUTES),
    )
    new_lock = section_lock_repo.create(db, new_lock)

    section = section_repo.get_by_id(db, section_id)
    if section:
        await manager.broadcast(
            section.schedule_id,
            {
                "type": "lock_acquired",
                "payload": {
                    "section_id": section_id,
                    "locked_by": user_id,
                    "display_name": display_name,
                    "expires_at": new_lock.expires_at.isoformat(),
                },
            },
        )

    return new_lock


async def release_lock(db: Session, section_id: int, user_id: int) -> None:
    """Release a lock on a section and broadcast lock_released to connected clients.

    Args:
        db: Database session.
        section_id: ID of the section to unlock.
        user_id: ID of the user releasing the lock.

    Raises:
        PermissionError: If the caller does not own the lock.
    """
    existing_lock = section_lock_repo.get_by_section_id(db, section_id)

    if existing_lock is None or existing_lock.locked_by != user_id:
        raise PermissionError("User does not own this lock")

    section_lock_repo.delete(db, existing_lock)

    section = section_repo.get_by_id(db, section_id)
    if section:
        await manager.broadcast(
            section.schedule_id,
            {"type": "lock_released", "payload": {"section_id": section_id}},
        )


def verify_lock(db: Session, section_id: int, user_id: int) -> None:
    """
    Verify that the caller owns the active lock on a section.

    Args:
        db: Database session.
        section_id: ID of the section to verify.
        user_id: ID of the user to verify ownership for.

    Raises:
        HTTPException: 403 if the caller does not own an active lock.
    """
    now = datetime.now(UTC).replace(tzinfo=None)
    existing_lock = section_lock_repo.get_by_section_id(db, section_id)

    if (
        existing_lock is None
        or existing_lock.expires_at < now
        or existing_lock.locked_by != user_id
    ):
        raise HTTPException(status_code=403, detail="User does not own this lock")


def get_active_locks_for_schedule(
    db: Session, schedule_id: int
) -> list[ScheduleActiveLockResponse]:
    """
    Return all active locks for a schedule with user display names.

    Args:
        db: Database session.
        schedule_id: ID of the schedule to query locks for.

    Returns:
        List of active locks with user display name included.
    """
    locks = section_lock_repo.get_active_by_schedule(db, schedule_id)
    result = []
    for lock in locks:
        user = db.query(User).filter(User.user_id == lock.locked_by).first()
        if not user:
            continue
        result.append(
            ScheduleActiveLockResponse(
                section_id=lock.section_id,
                locked_by=lock.locked_by,
                display_name=f"{user.first_name} {user.last_name}",
                expires_at=lock.expires_at,
            )
        )
    return result
