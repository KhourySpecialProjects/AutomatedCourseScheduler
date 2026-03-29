"""Comments router."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.services import comment as comment_service
from app.core.database import get_db
from app.models.comment import Comment
from app.models.section import Section
from app.models.user import User
from app.schemas.comment import CommentResponse, CommentSchema

router = APIRouter(prefix="/comments", tags=["comments"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""Post new comment under a particular section."""


@router.post("", response_model=CommentResponse, status_code=201)
def post_comment(commentIn: CommentSchema, db: Session = Depends(get_db)):
    try:
        posted = comment_service.post_comment(db, commentIn)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=e.args[0])

    return posted


"""Post a new comment reply."""


@router.post("/{parent_id}", response_model=CommentResponse, status_code=201)
def post_reply(parent_id: int, replyIn: CommentSchema, db: Session = Depends(get_db)):
    try:
        posted = comment_service.post_reply(db, replyIn, parent_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=e.args[0])

    return posted


"""Fetch comments for the given section"""


@router.get("/{section_id}", response_model=list[CommentResponse])
def get_comments(section_id: int, db: Session = Depends(get_db)):
    try:
        comments = comment_service.get_comments(db, section_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return comments


"""Delete the given comment"""


@router.delete("/{comment_id}", response_model=list[CommentResponse])
def delete_comment(comment_id: int, db: Session = Depends(get_db)):
    try:
        deleted = comment_service.delete_comment(db, comment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return deleted


"""Resolve the given comment"""


@router.put("/{comment_id}", status_code=204)
def resolve_comment(comment_id: int, db: Session = Depends(get_db)):
    try:
        comment_service.resolve_comment(db, comment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return
