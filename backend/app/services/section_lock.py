"""Section lock service — business logic."""

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.section_lock import SectionLock
from app.models.user import User
from app.repositories import section_lock as section_lock_repo
from app.schemas.section_lock import ScheduleActiveLockResponse


class SectionLockConflictError(Exception):
    """Raised when a section is locked by another user."""

    def __init__(self, lock: SectionLock):
        self.lock = lock


def acquire_lock(db: Session, section_id: int, user_id: int) -> SectionLock:
    """
    Acquire a lock on a section for editing and auto-releases any other lock the user
    currently holds onto.

    Args:
        db: Database connection.
        section_id: ID of the section to lock.
        user_id: ID of the user acquiring the lock.

    Returns:
        The acquired or refreshed SectionLock.

    Raises:
        SectionLockConflictError: If the section is locked by another user.
    """
    now = datetime.now(UTC).replace(tzinfo=None)
    existing_lock = section_lock_repo.get_by_section_id(db, section_id)

    # lock exists and is active
    if existing_lock and existing_lock.expires_at > now:
        # if same user, refresh the timer
        if existing_lock.locked_by == user_id:
            existing_lock.expires_at = now + timedelta(minutes=settings.LOCK_TIMEOUT_MINUTES)
            return section_lock_repo.save(db, existing_lock)
        # if different user, raise exception
        raise SectionLockConflictError(existing_lock)

    # lock doesn't exist or lock is expired
    # auto-release any other lock this user holds on a different section
    user_existing_lock = section_lock_repo.get_by_user_id(db, user_id)
    if user_existing_lock:
        # TODO: broadcast lock released once SSIP-70 is ready
        section_lock_repo.delete(db, user_existing_lock)

    # delete expired lock on this section if one exists
    if existing_lock:
        section_lock_repo.delete(db, existing_lock)

    # insert new lock
    new_lock = SectionLock(
        section_id=section_id,
        locked_by=user_id,
        expires_at=now + timedelta(minutes=settings.LOCK_TIMEOUT_MINUTES),
    )
    # TODO: broadcast lock acquired once SSIP-70 is ready
    return section_lock_repo.create(db, new_lock)


def release_lock(db: Session, section_id: int, user_id: int) -> None:
    """
    Release a lock on a section.

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
    # TODO: broadcast lock_released once SSIP-70 is ready


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
        user = db.query(User).filter(User.nuid == lock.locked_by).first()
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
