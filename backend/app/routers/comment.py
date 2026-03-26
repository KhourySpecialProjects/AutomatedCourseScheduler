"""Comment router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.comment import Comment, CommentCreate

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get("", response_model=list[Comment])
def get_comments(
    schedule_id: int | None = Query(None, description="Filter by schedule ID"),
    db: Session = Depends(get_db),
):
    """Get comments, optionally filtered by schedule."""
    # TODO: Implement comment listing
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("", response_model=CommentCreate, status_code=201)
def create_comment(comment: CommentCreate, db: Session = Depends(get_db)):
    """Create a new comment on a schedule component."""
    # TODO: Implement comment creation
    raise HTTPException(status_code=501, detail="Not implemented yet")
