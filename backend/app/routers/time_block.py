"""Time Block router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.time_block import TimeBlockResponse

router = APIRouter(prefix="/time-blocks", tags=["time-blocks"])


@router.get("", response_model=list[TimeBlockResponse])
def get_time_blocks(
    campus_id: int | None = Query(None, description="Filter by campus ID"),
    db: Session = Depends(get_db),
):
    """Retrieve all time blocks, optionally filtered by campus."""
    raise HTTPException(status_code=501, detail="Not implemented yet")
