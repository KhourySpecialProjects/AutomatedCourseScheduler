"""Comments router."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.comment import CommentResponse, CommentSchema
from app.services import comment as comment_service
from app.services import section as section_service
from app.services.connection_manager import manager

router = APIRouter(prefix="/comments", tags=["comments"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _broadcast_comment(db: Session, section_id: int, event_type: str, payload: dict) -> None:
    """Resolve section → schedule and broadcast a comment event."""
    section = section_service.get_by_id(db, section_id)
    if section:
        await manager.broadcast(section.schedule_id, {"type": event_type, "payload": payload})


@router.post("", response_model=CommentResponse, status_code=201)
async def post_comment(commentIn: CommentSchema, db: Session = Depends(get_db)):
    try:
        posted = comment_service.post_comment(db, commentIn)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=e.args[0]) from e

    await _broadcast_comment(
        db,
        commentIn.section_id,
        "comment_added",
        CommentResponse.model_validate(posted).model_dump(mode="json"),
    )
    return posted


@router.post("/{parent_id}", response_model=CommentResponse, status_code=201)
async def post_reply(parent_id: int, replyIn: CommentSchema, db: Session = Depends(get_db)):
    try:
        posted = comment_service.post_reply(db, replyIn, parent_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=e.args[0]) from e

    await _broadcast_comment(
        db,
        replyIn.section_id,
        "comment_added",
        CommentResponse.model_validate(posted).model_dump(mode="json"),
    )
    return posted


@router.get("/{section_id}", response_model=list[CommentResponse])
def get_comments(section_id: int, db: Session = Depends(get_db)):
    try:
        return comment_service.get_comments(db, section_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.delete("/{comment_id}", response_model=list[CommentResponse])
async def delete_comment(comment_id: int, db: Session = Depends(get_db)):
    comment = comment_service.get_by_id(db, comment_id)
    try:
        deleted = comment_service.delete_comment(db, comment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    if comment:
        await _broadcast_comment(
            db,
            comment.section_id,
            "comment_deleted",
            {"comment_id": comment_id, "section_id": comment.section_id},
        )
    return deleted


@router.put("/{comment_id}", status_code=204)
async def resolve_comment(comment_id: int, db: Session = Depends(get_db)):
    comment = comment_service.get_by_id(db, comment_id)
    try:
        comment_service.resolve_comment(db, comment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    if comment:
        await _broadcast_comment(
            db,
            comment.section_id,
            "comment_resolved",
            {"comment_id": comment_id, "section_id": comment.section_id},
        )
    # TODO: comment_updated broadcast when content editing is implemented
