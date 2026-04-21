from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.comment import Comment
from app.models.section import Section
from app.schemas.comment import CommentResponse, CommentSchema


def get_all(db: Session) -> list[Comment]:
    return db.query(Comment).all()


def count_active_by_schedule(db: Session, schedule_id: int) -> dict[int, int]:
    """Return mapping section_id -> number of active comments for all sections in the schedule."""
    rows = (
        db.query(Comment.section_id, func.count(Comment.comment_id))
        .join(Section, Comment.section_id == Section.section_id)
        .filter(Section.schedule_id == schedule_id, Comment.active.is_(True))
        .group_by(Comment.section_id)
        .all()
    )
    return {int(sid): int(n) for sid, n in rows}


def get_by_section(db: Session, section_id: int) -> list[Comment]:
    stmt = select(Comment).join(Section.comments).where(Comment.section_id == section_id, Comment.active.is_(True)).options(joinedload(Comment.user))
    results = db.scalars(stmt).all()
    return results


def get_by_id(db: Session, comment_id: int) -> Comment | None:
    stmt = select(Comment).where(Comment.comment_id == comment_id).options(joinedload(Comment.user))
    comment = db.scalars(stmt).first()
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
    db.refresh(comment, attribute_names=["user"])

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
    db.refresh(reply, attribute_names=["user"])

    return reply


def delete_comment(db: Session, comment: Comment) -> list[Comment]:
    """Soft-delete a comment.
    deleting a parent also soft-deletes its direct replies.
    """
    comment.active = False
    deleted: list[Comment] = [comment]
    for reply in list(comment.replies):
        reply.active = False
        deleted.append(reply)
    db.commit()
    for c in deleted:
        db.refresh(c)
    return deleted


def resolve_comment(db: Session, comment: CommentSchema) -> list[CommentResponse]:
    comment.resolved = True
    replies = comment.replies

    for reply in replies:
        reply.resolved = True

    all = [comment] + replies
    db.commit()

    for comment in all:
        db.refresh(comment)

    return all
