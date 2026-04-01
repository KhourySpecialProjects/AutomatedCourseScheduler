"""Section lock service — business logic."""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.section_lock import SectionLock
from app.repositories import section_lock as section_lock_repo


class SectionLockConflictError(Exception):
    """Raised when a section is locked by another user."""

    def __init__(self, lock: SectionLock):
        self.lock = lock


def acquire_lock(db: Session, section_id: int, user_id: int) -> SectionLock:
    """Acquire a lock on a section for editing.

    Three cases:
    - No lock or expired lock -> insert new lock
    - Lock held by another user -> raise SectionLockConflictError
    - Lock held by same user -> refresh expires_at

    Also auto-releases any other lock the user currently holds upon successfully
    acquiring a lock.
    """
    now = datetime.now(datetime.UTC)
    existing_lock = section_lock_repo.get_by_section_id(db, section_id)

    # lock exists and is active
    if existing_lock and existing_lock.expires_at > now:
        # if same user, refresh the timer
        if existing_lock.locked_by == user_id:
            existing_lock.expires_at = now + timedelta(
                minutes=settings.LOCK_TIMEOUT_MINUTES
            )
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
