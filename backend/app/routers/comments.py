"""Comments router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.comment import Comment
from app.models.section import Section
from app.models.user import User
from app.schemas.comment import CommentCreate

router = APIRouter(prefix="/comments", tags=["comments"])


"""Post new comment."""


@router.post("", response_model=CommentCreate)
def post_comment(
    user_id: int, content: str, section_id: int, db: Session = Depends(get_db)
):
    errors = []
    user = db.query(User).filter(User.nuid == user_id).first()
    section = db.query(Section).filter(Section.section_id == section_id).first()
    if not user:
        errors.append(f"User with id '{user_id}' not found")
    if not section:
        errors.append(f"Section with id '{section_id} not found")
    comment = Comment(user_id=user_id, content=content, section_id=section_id)
    db.add(comment)
    db.commit()


"""Post a new comment reply."""


@router.post("", response_model=CommentCreate)
def post_reply(
    user_id: int,
    content: str,
    section_id: int,
    parent: int,
    db: Session = Depends(get_db),
):
    # TODO: Implement comment replies
    raise HTTPException(status_code=501, detail="Not implemented yet")


"""Fetch comments for the given section"""


@router.get("", response_model=Comment)
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
