"""Comments router."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

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
def post_comment(commentIn: CommentSchema, db: Session = Depends(get_db)
                 ):
    errors = []
    user = db.query(User).filter(User.nuid == commentIn.user_id).first()
    section = db.query(Section).filter(
        Section.section_id == commentIn.section_id).first()
    if not user:
        errors.append(f"User with id '{commentIn.user_id}' not found")
    if not section:
        errors.append(f"Section with id '{commentIn.section_id}' not found")

    if errors:
        raise HTTPException(status_code=422, detail=errors)

    comment = Comment(user_id=commentIn.user_id,
                      content=commentIn.content, section_id=commentIn.section_id)

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return comment


"""Post a new comment reply."""


@router.post("/{parent_id}", response_model=CommentResponse, status_code=201)
def post_reply(parent_id: int, replyIn: CommentSchema, db: Session = Depends(get_db)):
    errors = []
    user = db.query(User).filter(User.nuid == replyIn.user_id).first()
    section = db.query(Section).filter(
        Section.section_id == replyIn.section_id).first()
    parent_comment = db.query(Comment).filter(
        Comment.comment_id == parent_id).first()
    if not user:
        errors.append(f"User with id '{replyIn.user_id}' not found")
    if not section:
        errors.append(f"Section with id '{replyIn.section_id}' not found")
    if not parent_comment:
        errors.append(
            f"Parent comment with id '{parent_id}' not found")

    if errors:
        raise HTTPException(status_code=422, detail=errors)

    reply = Comment(user_id=replyIn.user_id,
                    content=replyIn.content,
                    section_id=replyIn.section_id,
                    parent_id=parent_id)

    db.add(reply)
    db.commit()
    db.refresh(reply)

    return reply


"""Fetch comments for the given section"""


@router.get("/{section_id}", response_model=list[CommentResponse])
def get_comments(section_id: int, db: Session = Depends(get_db)):
    section = db.query(Section).filter(
        Section.section_id == section_id).first()
    if not section:
        raise HTTPException(
            status_code=404, detail=f"Section with id {section_id} not found")
    stmt = select(Comment).join(Section.comments).where(
        Comment.section_id == section_id)
    results = db.scalars(stmt).all()
    logger.error(results)
    print(results)

    return results


"""Delete the given comment"""


@router.delete("/{comment_id}", response_model=list[CommentResponse])
def delete_comment(comment_id: int, db: Section = Depends(get_db)):
    comment = db.get(Comment, comment_id)
    if comment:
        comment.active = False
    else:
        raise HTTPException(
            status_code=404, detail=f"Comment with id '{comment_id} not found")

    replies = comment.replies

    for reply in replies:
        reply.active = False

    all = [comment] + replies
    # logger.error(all)
    # logger.error("hello?")
    # print("BREIOPufopiu")
    db.commit()

    for comment in all:
        db.refresh(comment)

    return all


"""Resolve the given comment"""


@router.put("/{comment_id}", response_model=list[CommentResponse])
def resolve_comment(comment_id: int, db: Session = Depends(get_db)):
    comment = db.get(Comment, comment_id)
    if comment:
        comment.resolved = True
        db.commit()
        db.refresh(comment)
    else:
        raise HTTPException(
            status_code=404, detail=f"Comment with id '{comment_id} not found")

    replies = comment.replies

    for reply in replies:
        reply.resolved = True
        logger.error(reply)

    all = [comment] + replies
    db.commit()

    for comment in all:
        db.refresh(comment)

    return all
