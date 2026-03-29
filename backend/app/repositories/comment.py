from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.section import Section
from app.schemas.comment import CommentSchema, CommentResponse


def get_all(db: Session) -> list[Comment]:
    return db.query(Comment).all()


def get_by_section(db: Session, section_id: int) -> list[Comment]:
    stmt = (
        select(Comment).join(Section.comments).where(
            Comment.section_id == section_id)
    )
    results = db.scalars(stmt).all()
    return results


def get_by_id(db: Session, comment_id: int) -> Comment | None:
    comment = db.get(Comment, comment_id)
    return comment


def get_replies(db: Session, comment: Comment) -> list[Comment] | None:
    replies = comment.replies
    return replies


def post_comment(db: Session, commentIn: CommentSchema) -> CommentResponse:
    comment = Comment(
        user_id=commentIn.user_id,
        content=commentIn.content,
        section_id=commentIn.section_id,
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return comment


def post_reply(db: Session, replyIn: CommentSchema, parent_id: int) -> CommentResponse:
    reply = Comment(
        user_id=replyIn.user_id,
        content=replyIn.content,
        section_id=replyIn.section_id,
        parent_id=parent_id,
    )

    db.add(reply)
    db.commit()
    db.refresh(reply)

    return reply


def delete_comment(db: Session, comment: Comment) -> list[CommentResponse]:
    comment.active = False
    replies = comment.replies

    for reply in replies:
        reply.active = False

    all = [comment] + replies
    db.commit()

    for comment in all:
        db.refresh(comment)

    return all


def resolve_comment(db: Session, comment: CommentSchema) -> list[CommentResponse]:
    comment.resolved = True
    replies = comment.replies

    for reply in replies:
        reply.resolved = True
        logger.error(reply)

    all = [comment] + replies
    db.commit()

    for comment in all:
        db.refresh(comment)

    return all
