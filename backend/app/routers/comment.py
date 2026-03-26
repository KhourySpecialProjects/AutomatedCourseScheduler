"""Comments router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.comment import Comment
from app.models.section import Section
from app.models.user import User
from app.schemas.comment import CommentResponse, CommentSchema

router = APIRouter(prefix="/comments", tags=["comments"])


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
        errors.append(f"Section with id '{commentIn.section_id} not found")

    if errors:
        raise HTTPException(status_code=422, detail=errors)

    comment = Comment(user_id=commentIn.user_id,
                      content=commentIn.content, section_id=commentIn.section_id)

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return comment


"""Post a new comment reply."""


@router.post("", response_model=CommentResponse)
def post_reply(replyIn: CommentSchema, db: Session = Depends(get_db)):
    # TODO: Implement comment replies
    errors = []
    user = db.query(User).filter(User.nuid == replyIn.user_id).first()
    section = db.query(Section).filter(
        Section.section_id == replyIn.section_id).first()
    parent_comment = db.query(Comment).filter(
        Comment.comment_id == replyIn.parent_id).first()
    if not user:
        errors.append(f"User with id '{replyIn.user_id}' not found")
    if not section:
        errors.append(f"Section with id '{replyIn.section_id}' not found")
    if not parent_comment:
        errors.append(
            f"Parent comment with id '{replyIn.parent_id}' not found")

    if errors:
        raise HTTPException(status_code=422, detail=errors)

    reply = Comment(user_id=replyIn.user_id,
                    content=replyIn.content,
                    section_id=replyIn.section_id,
                    parent_id=replyIn.parent_id)

    db.add(reply)
    db.commit()
    db.refresh(reply)

    return reply


"""Fetch comments for the given section"""


@router.get("", response_model=list[CommentSchema])
def get_comments(section_id: int, db: Session = Depends(get_db)):
    # TODO: Implement comment listing
    raise HTTPException(status_code=501, detail="Not implemented yet")


"""Delete the given comment"""


@router.delete(
    "",
)
def delete_comment(comment_id: int, db: Section = Depends(get_db)):
    # TODO: Implement comment deletion
    raise HTTPException(status_code=501, detail="Not implemented yet")


"""Resolve the given comment"""


@router.put(
    "",
)
def resolve_comment(comment_id: int, db: Session = Depends(get_db)):
    # TODO: Implement comment resolution
    raise HTTPException(status_code=501, detail="Not implemented yet")
