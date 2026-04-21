"""Time Block router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.time_block import TimeBlockCreate, TimeBlockResponse, TimeBlockUpdate
from app.services import time_block as time_block_service
from app.services.time_block import BlockGroupConflictError

router = APIRouter(prefix="/time-blocks", tags=["time-blocks"])


@router.get("", response_model=list[TimeBlockResponse])
def get_time_blocks(
    campus_id: int | None = Query(None, description="Filter by campus ID"),
    db: Session = Depends(get_db),
):
    """Retrieve all time blocks, optionally filtered by campus."""
    return time_block_service.get_time_blocks(db, campus_id=campus_id)


@router.post("", response_model=TimeBlockResponse, status_code=201)
def create_time_block(body: TimeBlockCreate, db: Session = Depends(get_db)):
    """Create a new time block.

    `meeting_days` should be a compact uppercase day string (e.g. "MWF", "TR").
    `start_time` and `end_time` must be in HH:MM format.
    Set `block_group` to the same 8-character hex string on two rows to mark
    them as a split block pair — split blocks are excluded from auto-assignment.
    Returns 409 if the block_group already has a complete pair on this campus.
    """
    try:
        return time_block_service.create_time_block(db, body)
    except BlockGroupConflictError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.patch("/{time_block_id}", response_model=TimeBlockResponse)
def update_time_block(time_block_id: int, body: TimeBlockUpdate, db: Session = Depends(get_db)):
    """Partially update a time block.  Only fields present in the request body are changed."""
    try:
        updated = time_block_service.update_time_block(db, time_block_id, body)
    except BlockGroupConflictError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if updated is None:
        raise HTTPException(status_code=404, detail="Time block not found")
    return updated


@router.delete("/{time_block_id}", status_code=204)
def delete_time_block(time_block_id: int, db: Session = Depends(get_db)):
    """Delete a time block.

    Returns 400 if any sections are currently assigned to this block —
    those sections must be reassigned or removed first.
    """
    try:
        deleted = time_block_service.delete_time_block(db, time_block_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not deleted:
        raise HTTPException(status_code=404, detail="Time block not found")
    return None
