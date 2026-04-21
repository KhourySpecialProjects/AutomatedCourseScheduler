"""Time block service — business logic for time block management."""

from datetime import time

from sqlalchemy.orm import Session

from app.models.time_block import TimeBlock
from app.repositories import time_block as time_block_repo
from app.schemas.time_block import TimeBlockCreate, TimeBlockResponse, TimeBlockUpdate


def _parse_time(value: str) -> time:
    """Parse a "HH:MM" string into a Python time object.

    Raises ValueError with a descriptive message if the format is invalid.
    """
    try:
        parts = value.strip().split(":")
        if len(parts) != 2:
            raise ValueError
        return time(int(parts[0]), int(parts[1]))
    except (ValueError, TypeError):
        raise ValueError(f"Time must be in HH:MM format, got '{value}'") from None


def _to_response(tb: TimeBlock) -> TimeBlockResponse:
    """Convert a TimeBlock ORM object to a TimeBlockResponse schema."""
    return TimeBlockResponse(
        time_block_id=tb.time_block_id,
        meeting_days=tb.meeting_days,
        # Format time fields as "HH:MM" strings for consistent API output
        start_time=tb.start_time.strftime("%H:%M"),
        end_time=tb.end_time.strftime("%H:%M"),
        campus_id=tb.campus,
        block_group=tb.block_group,
    )


def get_time_blocks(db: Session, campus_id: int | None = None) -> list[TimeBlockResponse]:
    """Return all time blocks, optionally filtered by campus."""
    if campus_id is not None:
        blocks = time_block_repo.get_by_campus(db, campus_id)
    else:
        blocks = time_block_repo.get_all(db)
    return [_to_response(tb) for tb in blocks]


def create_time_block(db: Session, body: TimeBlockCreate) -> TimeBlockResponse:
    """Create and persist a new time block.

    Validates that start_time is before end_time and that the meeting_days
    string contains at least one alphabetic day character.
    """
    start = _parse_time(body.start_time)
    end = _parse_time(body.end_time)

    if start >= end:
        raise ValueError("start_time must be before end_time")

    # Ensure meeting_days contains at least one valid day letter
    days = [c for c in body.meeting_days.strip().upper() if c.isalpha()]
    if not days:
        raise ValueError("meeting_days must contain at least one day letter (e.g. 'MWF')")

    tb = TimeBlock(
        meeting_days=body.meeting_days.strip().upper(),
        start_time=start,
        end_time=end,
        campus=body.campus_id,
        block_group=body.block_group,
    )
    time_block_repo.create(db, tb)
    return _to_response(tb)


def update_time_block(
    db: Session, time_block_id: int, body: TimeBlockUpdate
) -> TimeBlockResponse | None:
    """Partially update a time block.  Returns None if the block is not found.

    Only fields explicitly included in the request body are updated.
    """
    tb = time_block_repo.get_by_id(db, time_block_id)
    if tb is None:
        return None

    fields = body.model_fields_set

    if "meeting_days" in fields:
        if not body.meeting_days:
            raise ValueError("meeting_days is invalid")
        days = [c for c in body.meeting_days.strip().upper() if c.isalpha()]
        if not days:
            raise ValueError("meeting_days must contain at least one day letter")
        tb.meeting_days = body.meeting_days.strip().upper()

    if "start_time" in fields:
        if not body.start_time:
            raise ValueError("start_time is invalid")
        tb.start_time = _parse_time(body.start_time)

    if "end_time" in fields:
        if not body.end_time:
            raise ValueError("end_time is invalid")
        tb.end_time = _parse_time(body.end_time)

    # Validate ordering after applying any time changes
    if tb.start_time >= tb.end_time:
        raise ValueError("start_time must be before end_time")

    if "campus_id" in fields:
        if body.campus_id is None:
            raise ValueError("campus_id is invalid")
        tb.campus = body.campus_id

    if "block_group" in fields:
        # Allows explicitly setting block_group to None to unlink a split block
        tb.block_group = body.block_group

    time_block_repo.save(db, tb)
    return _to_response(tb)


def delete_time_block(db: Session, time_block_id: int) -> bool:
    """Delete a time block.  Returns False if the block does not exist.

    Raises ValueError if sections are currently assigned to this block —
    those sections must be reassigned or deleted first.
    """
    tb = time_block_repo.get_by_id(db, time_block_id)
    if tb is None:
        return False

    if time_block_repo.has_sections(db, time_block_id):
        raise ValueError(
            "Time block has sections assigned to it and cannot be deleted. "
            "Reassign or remove those sections first."
        )

    time_block_repo.delete(db, tb)
    return True
